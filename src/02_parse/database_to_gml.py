#!/usr/bin/env python

import os
import sys

import lxml.html
import pprint
import ipdb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import networkx as nx
import itertools

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
ROOT_URI = "http://www.metafilter.com"

CURRENT_DIR = os.path.join(__file__, os.pardir)
SRC_DIR = os.path.join(CURRENT_DIR, os.pardir)

# Imports from scrape.
SCRAPE_SRC_DIR = os.path.abspath(os.path.join(SRC_DIR, "01_scrape"))
sys.path.append(SCRAPE_SRC_DIR)
import models

DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir, "data"))
DATABASE_PATH = os.path.abspath(os.path.join(DATA_DIR, "database.sqlite3"))
DATABASE_URI = "sqlite:///%s" % DATABASE_PATH

FAVORITES_GML_OUTPUT_PATH = os.path.abspath(os.path.join(DATA_DIR, "favorites.gml"))
COMMENTS_GML_OUTPUT_PATH = os.path.abspath(os.path.join(DATA_DIR, "comments.gml"))
# -----------------------------------------------------------------------------

def generate_favorites():
    """Output an undirected graph where nodes are users and an edge is drawn
    if two users have ever favorited the same post on MetaFilter."""

    print "generate_favorites() entry."

    # -------------------------------------------------------------------------
    #   Get all the Post objects.
    # -------------------------------------------------------------------------
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind = engine)
    session = Session()
    posts = session.query(models.Post)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Parse all their favorites pages using lxml.html.
    #   Add respective nodes to an undirected graph.
    # -------------------------------------------------------------------------
    G = nx.Graph()
    for post in posts:
        if post.favorites_text is None:
            continue
        doc = lxml.html.document_fromstring(post.favorites_text)
        doc.make_links_absolute(ROOT_URI)
        all_links = [elem for elem in doc.cssselect("a")]
        user_links = [elem for elem in all_links
                      if  hasattr(elem, "attrib")
                      and elem.attrib is not None
                      and elem.attrib.get("href", None) is not None
                      and r"/user/" in elem.attrib["href"]]
        user_ids = []
        for user_link in user_links:
            href = user_link.attrib["href"]
            user_id = int(href.split(r"/")[-1])
            user_ids.append(user_id)
        user_id_combinations = itertools.combinations(user_ids, r=2)
        for (first_node, second_node) in user_id_combinations:
            G.add_edge(first_node, second_node)
    # -------------------------------------------------------------------------

    nx.write_gml(G, FAVORITES_GML_OUTPUT_PATH)

def generate_comments():
    """Output an undirected graph where nodes are users and an edge is drawn
    if two users have ever commented on the same post on MetaFilter."""

    print "generate_comments() entry."

    # -------------------------------------------------------------------------
    #   Get all the Post objects.
    # -------------------------------------------------------------------------
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind = engine)
    session = Session()
    posts = session.query(models.Post)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Parse all their comments using lxml.html.
    #   Add respective nodes to an undirected graph.
    # -------------------------------------------------------------------------
    G = nx.Graph()
    for post in posts:
        if post.text is None:
            continue
        doc = lxml.html.document_fromstring(post.text)
        doc.make_links_absolute(ROOT_URI)
        user_links = [link for link in doc.cssselect(".comments .smallcopy a")
                      if r"/user/" in link.attrib["href"]]
        user_ids = []
        for user_link in user_links:
            href = user_link.attrib["href"]
            user_id = int(href.split(r"/")[-1])
            user_ids.append(user_id)
        user_id_combinations = itertools.combinations(user_ids, r=2)
        for (first_node, second_node) in user_id_combinations:
            G.add_edge(first_node, second_node)
    # -------------------------------------------------------------------------

    nx.write_gml(G, COMMENTS_GML_OUTPUT_PATH)

def main():
    generate_favorites()
    generate_comments()

if __name__ == "__main__":
    main()
