#!/bin/sh
set -e

# Script for the docker endpoint, waits for the db, and executes whatever command.

db_wait() {
    # Wait for postgres to come online
    until PGPASSWORD=uchan psql -h db -U "uchan" -c '\l' >/dev/null; do
        >&2 echo "Waiting for postgres to be ready"
        sleep 1
    done
}

case "$1" in
    "app")
        db_wait
        uwsgi /etc/uwsgi/uwsgi.ini
        ;;
    "worker")
        db_wait
        celery worker --uid uchan -c 8 -A uchan:celery --logfile=/opt/app/data/log/worker-%n.log --loglevel=INFO
        ;;
    "upgrade")
        db_wait
        alembic upgrade head
        ;;
    "setup")
        db_wait
        python3 setup.py
        ;;
    "shell")
        /bin/sh
        ;;
    "assets")
        ./assets.sh
        ;;
    *)
        exit 1
        ;;
esac
