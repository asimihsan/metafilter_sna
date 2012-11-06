#!/usr/bin/env bash

celeryd --concurrency=4 --maxtasksperchild=100 -A tasks --purge --soft-time-limit 10 --loglevel=INFO
