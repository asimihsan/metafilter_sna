# -----------------------------------------------------------------------------
#   Celery config file. Thie configuration affects how the distributed
#   task queue operates.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Per-task configuration.
# -----------------------------------------------------------------------------
CELERY_ANNOTATIONS = {
    "tasks.get_uri": {
        "rate_limit": "1/s",
    },
}
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Use the "py-amqp" library to connect to an AMQP broker running locally
#   (i.e. 'localhost') using "guest" as both the username and password.
#
#   This usually means you've installed RabbitMQ locally.
# -----------------------------------------------------------------------------
BROKER_URL = "pyamqp://guest@localhost//"
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   How to store task results.
# -----------------------------------------------------------------------------
CELERY_RESULT_BACKEND = "amqp"
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   How to serialize tasks. We're only connecting Python tasks to our queue
#   so don't waste time serializing as json, just pickle it.
# -----------------------------------------------------------------------------
CELERY_TASK_SERIALIZER = "pickle"
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Miscellanea.
# -----------------------------------------------------------------------------
CELERY_TIMEZONE = "Europe/London"
CELERY_ENABLE_UTC = True
CELERY_DEFAULT_EXCHANGE = "celery_metafilter_sna"
CELERY_RESULT_EXCHANGE = "celeryresults_metafilter_sna"
CELERY_TASK_RESULT_EXPIRES = 60
# -----------------------------------------------------------------------------

