from database.services import insert_market_hash_names
from config import REDIS_PORT, REDIS_HOST

from celery import Celery

from celery.schedules import crontab
import asyncio

celery = Celery('tasks', broker=f'redis://{REDIS_HOST}:{REDIS_PORT}')


@celery.task
async def get_market_hash_names():
    asyncio.run(insert_market_hash_names())


celery.conf.beat_schedule = {
    'run-task-every-day': {
        'task': 'get_market_hash_names',
        'schedule': crontab(hour=12, minute=0),
    },
}

# celery -A tasks.tasks:celery worker --loglevel=INFO
# celery -A tasks.tasks:celery flower
