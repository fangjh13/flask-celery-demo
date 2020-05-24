#!/usr/bin/env bash

source venv/bin/activate


function start_flask {
    exec flask run -p 5000 -h 0.0.0.0
}

function start_worker {
    exec celery worker --app=service.my_celery --pool=gevent --concurrency=20 --loglevel=INFO
}

function start_beat {
    exec celery beat --app=service.my_celery --loglevel=INFO
}

case $1 in
    flask*)
      start_flask
      ;;
    celery-worker*)
      start_worker
      ;;
    celery-beat*)
      start_beat
      ;;
    *)
      echo run failed !
      ;;
esac