import pendulum
from redis import Redis
from rq_scheduler import Scheduler
from tasks import fetch_recently_played_and_store

scheduler = Scheduler(connection=Redis())
job_id = "fetch_recent_every_30min"

existing_jobs = scheduler.get_jobs()
for job in existing_jobs:
    if job.id == job_id:
        print(f"Job {job_id} already exists, skipping.")
        break
else:
    scheduler.schedule(
        scheduled_time=pendulum.now().add(seconds=5),
        func=fetch_recently_played_and_store,
        args=[],
        interval=1800,  # every 30 min
        repeat=None,
        id=job_id,
    )
    print("Recurring job scheduled: fetch_recent_every_30min")
