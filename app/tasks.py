"""
`tasks.py`
define celery tasks here
"""

from service import my_celery as celery
from typing import Any
import time
import random


@celery.task()
def log(message: Any) -> Any:
    return message


@celery.task()
def multiply(x: int, y: int) -> int:
    return x*y


@celery.task(bind=True, max_retries=2, default_retry_delay=5, time_limit=4)
def calc(self, n):
    try:
        sleep_time = random.random() * 5
        time.sleep(sleep_time)
        if sleep_time > 2.5:
            raise TimeoutError('timeout')
        return n + 1
    except TimeoutError as e:
        self.retry(exc=e)
