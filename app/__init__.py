from flask import Flask
from celery import Celery
from config import config


def create_app(config_name, **kwargs):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # initial celery
    if kwargs.get('celery'):
        init_celery(kwargs['celery'], app)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app


def init_celery(celery: Celery, app: Flask) -> None:
    """
    initial celery object wraps the task execution in an application context
    """
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


