#!/usr/bin/env bash

celeryd --events --concurrency=3 -A tasks --purge --soft-time-limit 120 --time-limit 180 --loglevel=INFO
