import os
import sys
import requests
import httplib2
import lxml.html
import pprint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import select, exists
import time
import bz2
import cPickle as pickle

import models

# ----------------------------------------------------------------------------
#   Constants.
# ----------------------------------------------------------------------------

# What is the front page.
ROOT_URI = "http://www.metafilter.com"

# How many pages of posts do you want.
DEPTH_LIMIT = 30

CURRENT_DIR = os.path.join(__file__, os.pardir)
DATA_DIR = os.path.join(CURRENT_DIR, os.pardir, os.pardir, "data")
DATABASE_PATH = os.path.abspath(os.path.join(DATA_DIR, "database.sqlite3"))
DATABASE_URI = "sqlite:///%s" % DATABASE_PATH

# If you need a proxy set it up here. Else set this variable to None.
PROXY = None
#PROXY = (httplib2.socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#   Configure the Celery tasks using celeryconfig.py.
# ----------------------------------------------------------------------------
from celery import Celery
celery = Celery()
celery.config_from_object('celeryconfig')
# ----------------------------------------------------------------------------

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@celery.task
def initialize_database(name="tasks.initialize_database"):
    engine = create_engine(DATABASE_URI)
    models.Base.metadata.create_all(engine)

    # -------------------------------------------------------------------------
    #   Delete empty Post objects, i.e. if there aren't any favorites_text then
    #   we never got round to finishing them.
    # -------------------------------------------------------------------------
    logger.info("delete empty Post objects.")
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind = engine)
    session = Session()
    empty_posts = session.query(models.Post).filter_by(favorites_text = None)
    for empty_post in empty_posts:
        session.delete(empty_post)
    session.commit()
    # -------------------------------------------------------------------------

@celery.task
def drop_database(name="tasks.drop_database"):
    engine = create_engine(DATABASE_URI)
    models.Base.metadata.drop_all(engine)

@celery.task
def get_uri(uri, **kwargs):
    """Get a URI and return its text content.

    This is wrapped in a task so that we can easily rate limit how often we
    hit the server."""
    logger.info("HTTP GET for URI: '%s'" % uri)
    if uri is None:
        logger.warning("URI is None.")
        return None
    try:
        if PROXY:
            conn = httplib2.Http(proxy_info = httplib2.ProxyInfo(PROXY[0],
                                                                 PROXY[1],
                                                                 PROXY[2]))
        else:
            conn = httplib2.Http()
        response, content = conn.request(uri)
        if not response["status"].startswith("2"):
            logger.error("bad status code: %s" % response["status"])
            return None
    except Exception, exc:
        logger.exception("unhandled exception.")
        get_uri.retry(args=(uri, ), exc=exc, kwargs=kwargs)
    return bz2.compress(content)

@celery.task
def get_post_uris(root_uri = ROOT_URI,
                  current_uri = ROOT_URI,
                  depth_limit = DEPTH_LIMIT,
                  current_depth = 0,
                  all_post_uris = None):
    """Go to the root of MetaFilter and get the URIs for the front pages,
    i.e. those that contain the post summaries.

    Each time we encounter a front page scrape the URIs for each individual
    post, commit a Post object to the database, and then launch a
    parse_post task for that Post."""

    logger.info("entry. current_uri: %s, current_depth: %s" % (current_uri, current_depth))

    # -------------------------------------------------------------------------
    #   Initialize local variables.
    # -------------------------------------------------------------------------
    if all_post_uris == None:
        all_post_uris = []
    else:
        all_post_uris = pickle.loads(bz2.decompress(all_post_uris))
    # -------------------------------------------------------------------------

    if current_depth >= depth_limit:
        return

    # -------------------------------------------------------------------------
    #   Get the text of the URI.
    # -------------------------------------------------------------------------
    try:
        text = bz2.decompress(get_uri.delay(current_uri).get())
    except Exception, exc:
        get_post_uris.retry(exc=exc)
    doc = lxml.html.document_fromstring(text)
    doc.make_links_absolute(ROOT_URI)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Get a list of post URIs, add it to the list we have.
    # -------------------------------------------------------------------------
    post_uris = [link.attrib["href"] for link in doc.cssselect(".more")]
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind = engine)
    session = Session()
    for post_uri in post_uris:
        logger.info("considering processing post_uri: '%s'" % post_uri)
        existing_posts = session.query(models.Post).filter_by(uri = post_uri)
        if existing_posts.count() > 0 and \
           existing_posts.first().favorites_text is not None:
            logger.info("post_uri '%s' already exists and is processed." % post_uri)
            continue
        process_post.delay(post_uri)
        all_post_uris.append(post_uri)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Get the URI for "Older posts"
    # -------------------------------------------------------------------------
    next_link = [elem for elem in doc.cssselect("a")
                 if hasattr(elem, "text") and
                    elem.text is not None and
                    "Older posts" in elem.text]
    if len(next_link) == 0:
        logger.error("no next_link.")
        return
    next_link = next_link[0]
    logger.info("next_link points to: %s" % next_link.attrib["href"])
    if len(all_post_uris) > 0:
        logger.info("encountered some new posts yet.")
        current_depth += 1
        countdown = 10
    else:
        logger.info("have not encountered any new posts.")
        countdown = 0
    kwargs = {"root_uri": ROOT_URI,
              "current_uri": next_link.attrib["href"],
              "depth_limit": DEPTH_LIMIT,
              "current_depth": current_depth,
              "all_post_uris": bz2.compress(pickle.dumps(all_post_uris))}
    get_post_uris.apply_async(kwargs=kwargs, countdown=countdown)
    # -------------------------------------------------------------------------

@celery.task
def process_post(post_uri):
    logger.info("entry. post_uri: %s" % post_uri)

    # -------------------------------------------------------------------------
    #   If a Post with the same URI does not already exist then create
    #   a new Post object.
    # -------------------------------------------------------------------------
    logger.info("maybe create new Post object.")
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind = engine)
    session = Session()
    post = models.Post()
    session.add(post)
    session.commit()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Get the post_uri contents and then parse their contents.
    #
    #   Note this curious call. Why bother chain'ing, when we could just
    #   task.delay(*args).get() instead? i.e. why make an asynchronous
    #   call when a synchronous one would do?
    #
    #   Precisely because synchronous calls simply cause a deadlock due to
    #   all the workers getting used up waiting to launch more workers to
    #   get URIs.
    #
    #   Notice how def parse_post() seems to take three arguments, but
    #   we've only called it with two below. That because the pipe operator
    #   passes the result of the previous call as the first positional
    #   argument of the next function.
    #
    #   See: http://docs.celeryproject.org/en/master/userguide/tasks.html#avoid-launching-synchronous-subtasks
    # -------------------------------------------------------------------------
    chain = get_uri.s(post_uri) | \
            parse_post.s(post.id, post_uri) | \
            get_uri.s() | \
            store_post.s(post.id, post_uri)
    chain()
    # -------------------------------------------------------------------------

@celery.task
def parse_post(post_text, post_pk, post_uri):
    logger.info("entry. post_pk: %s, post_uri: %s" % (post_pk, post_uri))

    # -------------------------------------------------------------------------
    #   Initialize local variables.
    # -------------------------------------------------------------------------
    post_text = bz2.decompress(post_text)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Update the existing Post object.
    # -------------------------------------------------------------------------
    logger.info("updating Post object.")
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind = engine)
    session = Session()
    post = session.query(models.Post).filter_by(id = post_pk).first()
    post.uri = post_uri.decode("utf-8")
    post.text = post_text.decode("utf-8")
    session.add(post)
    session.commit()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Determine if there is a favourites link. If there is get the
    #   contents of the favorites URI.
    # -------------------------------------------------------------------------
    logger.info("check for favorites link...")
    doc = lxml.html.document_fromstring(post_text)
    doc.make_links_absolute(ROOT_URI)
    all_links = [elem for elem in doc.cssselect("a")]
    favorites_link = [elem for elem in all_links
                      if hasattr(elem, "text") and
                         elem.text is not None and
                         "marked this as a favorite" in elem.text]
    if len(favorites_link) == 0:
        logger.info("there is no favorites link.")
        return None
    favorites_link = favorites_link[0]
    return favorites_link.attrib["href"]
    # -------------------------------------------------------------------------

@celery.task
def store_post(favorites_text, post_pk, post_uri):
    logger.info("entry. post_pk: %s, post_uri: %s" % (post_pk, post_uri))

    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind = engine)
    session = Session()
    post = session.query(models.Post).filter_by(id = post_pk).first()

    if favorites_text is None:
        logger.info("post favorites is empty.")
        session.delete(post)
    else:
        logger.info("post favorites is not empty.")
        favorites_text = bz2.decompress(favorites_text)
        post.favorites_text = favorites_text.decode("utf-8")
        session.add(post)
    session.commit()

