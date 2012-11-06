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
        "default_retry_delay": "60",
        "max_retries": 3,
    },
}
                  
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Use the "py-amqp" library to connect to an AMQP broker running locally
#   (i.e. 'localhost') using "guest" as both the username and password.
#
#   This usually means you've installed RabbitMQ locally.
# -----------------------------------------------------------------------------
BROKER_URL = "pyamqp://guest:guest@127.0.0.1:5672//"
BROKER_HEARTBEAT = 10
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

