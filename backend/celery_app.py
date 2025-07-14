from celery import Celery

celery = Celery(
    'spotify_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['tasks']
)

# Route each task to a specific queue
celery.conf.task_routes = {
    'tasks.process_spotify_json_file': {'queue': 'uploads'},
    'tasks.update_user_snapshots': {'queue': 'snapshots'},
}
