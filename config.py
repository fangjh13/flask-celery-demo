from celery.schedules import crontab


class Config:

    @classmethod
    def init_app(cls, app):
        pass

    CELERY_BROKER_URL = "redis://redis:6379/0"
    CELERY_BACKEND_URL = "redis://redis:6379/1"
    CELERYBEAT_SCHEDULE = {
        'log-every-1-minutes': {
            'task': 'app.tasks.log',
            'schedule': crontab(minute="*/1"),
            'args': ("log every 1 minutes",)
        }
    }


class Development(Config):
    DEBUG = True


class Production(Config):
    pass


config = {
    'development': Development,
    'production': Production,

    'default': Production
}