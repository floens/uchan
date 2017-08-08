#!/bin/sh
set -e

# Script for the docker endpoint, waits for the db, and executes whatever command.

# Wait for postgres to come online
until PGPASSWORD=uchan psql -h db -U "uchan" -c '\l' >/dev/null; do
  >&2 echo "Waiting for postgres to be ready"
  sleep 1
done

case "$1" in
    "app")
        uwsgi /etc/uwsgi/uwsgi.ini
        ;;
    "worker")
        celery worker --uid uchan -c 8 -A uchan:celery --logfile=/opt/app/data/log/worker-%n.log --loglevel=INFO
        ;;
    "upgrade")
        alembic upgrade head
        ;;
    "setup")
        python3 setup.py
        ;;
    "shell")
        /bin/sh
        ;;
    "assets")
        tsc -p extra
        FLASK_APP=uchan/__init__.py flask assets build
        ;;
    *)
        exit 1
        ;;
esac
