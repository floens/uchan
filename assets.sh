#!/bin/bash

if [ "$1" = "watch" ]; then
    tsc -p extra -w &
    PIDS[0]=$!

    FLASK_APP=uchan/__init__.py flask assets watch &
    PIDS[1]=$!

    trap "kill ${PIDS[*]}" SIGINT
    wait
else
    tsc -p extra
    FLASK_APP=uchan/__init__.py flask assets build
fi
