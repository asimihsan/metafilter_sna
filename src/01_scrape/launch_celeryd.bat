@echo off
celeryd --concurrency=4 --maxtasksperchild=100 -A tasks --purge --time-limit 10 --loglevel=DEBUG
