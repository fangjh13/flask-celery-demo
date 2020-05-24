from . import api
from flask import jsonify
from celery.exceptions import TimeoutError
from app.tasks import log


@api.route("/hello-world")
def hello_world():
    result = log.delay('hello world')
    try:
        r = result.get(timeout=3)
    except TimeoutError:
        r = 'celery run failed'
    return jsonify({"info": r})
