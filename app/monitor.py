import os
import sys

# Add the project's root directory to the PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import redis
from rq import Queue
from rq.registry import StartedJobRegistry

redis_conn = redis.Redis()
queue = Queue(connection=redis_conn)

# Get the list of started jobs (active jobs)
started_job_registry = StartedJobRegistry("default", connection=redis_conn)
started_job_ids = started_job_registry.get_job_ids()

if started_job_ids:
    print("Active Jobs:")
    for job_id in started_job_ids:
        job = queue.fetch_job(job_id)
        if job:
            print(f"  Job ID: {job.id}, Function: {job.func_name}, Status: started")
        else:
            print(f"Job id: {job_id} not found")
else:
    print("No active jobs.")

# get the queued jobs.
queued_jobs = queue.get_job_ids()

if queued_jobs:
    print("Queued Jobs:")
    for job_id in queued_jobs:
        job = queue.fetch_job(job_id)
        if job:
            print(f"  Job ID: {job.id}, Function: {job.func_name}, Status: queued")
        else:
            print(f"Job id: {job_id} not found")
else:
    print("No queued jobs.")
