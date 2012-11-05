#!/usr/bin/env bash

celeryd --concurrency=4 --maxtasksperchild=4 -A tasks --purge --loglevel=INFO
