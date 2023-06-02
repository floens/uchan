#!/bin/bash
set -e

exec uwsgi --ini /app/docker/uwsgi.http.ini
