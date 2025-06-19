from celery import Celery


# Celery config

celery = Celery(
    'spotify_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery.conf.task_routes = {
    'tasks.process_spotify_json_file': {'queue': 'spotify'}
}

import tasks
