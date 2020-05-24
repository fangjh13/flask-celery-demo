import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print(f"load `{env_path}` environment file")
    load_dotenv(env_path)


from app import create_app
from celery import Celery
from config import config


def make_celery(app_name):
    broker = getattr(config[os.getenv('FLASK_ENV') or 'default'], "CELERY_BROKER_URL")
    backend = getattr(config[os.getenv('FLASK_ENV') or 'default'], "CELERY_BACKEND_URL")

    celery = Celery(
        app_name,
        broker=broker,
        backend=backend
    )

    return celery


# share celery object
my_celery = make_celery(__name__)

flask_app = create_app(os.getenv('FLASK_ENV') or 'default', celery=my_celery)


