import os
import sys
import redis
from rq import Queue
from rq.registry import StartedJobRegistry
from datetime import datetime

# Add the project's root directory to the PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Connect to Redis
redis_conn = redis.Redis()
queue = Queue(connection=redis_conn)


def print_section_header(title):
    """Print a formatted section header."""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")


def monitor_jobs():
    """Monitor and print active and queued jobs."""
    # Get the list of started jobs (active jobs)
    started_job_registry = StartedJobRegistry("default", connection=redis_conn)
    started_job_ids = started_job_registry.get_job_ids()

    if started_job_ids:
        print_section_header("Active Jobs")
        for job_id in started_job_ids:
            job = queue.fetch_job(job_id)
            if job:
                print(f"  Job ID: {job.id}, Function: {job.func_name}, Status: started")
            else:
                print(f"Job id: {job_id} not found")
    else:
        print_section_header("Active Jobs")
        print("No active jobs.")

    # Get queued jobs
    queued_jobs = queue.get_job_ids()

    if queued_jobs:
        print_section_header("Queued Jobs")
        for job_id in queued_jobs:
            job = queue.fetch_job(job_id)
            if job:
                print(f"  Job ID: {job.id}, Function: {job.func_name}, Status: queued")
            else:
                print(f"Job id: {job_id} not found")
    else:
        print_section_header("Queued Jobs")
        print("No queued jobs.")


def monitor_users():
    """Monitor and print registered users."""
    print_section_header("Registered Users")

    # Scan for all user keys
    user_keys = redis_conn.keys("user:*")

    if not user_keys:
        print("No registered users found.")
        return

    for key in user_keys:
        # Decode the key and extract user ID
        user_id = key.decode("utf-8").split(":")[1]

        # Get user details
        user_details = redis_conn.hgetall(key)

        # Decode and process user details
        decoded_details = {
            k.decode("utf-8"): v.decode("utf-8") for k, v in user_details.items()
        }

        # Prepare user status
        status = "Active" if decoded_details.get("active") == "true" else "Inactive"

        print(f"User ID: {user_id}")
        print(f"  Status: {status}")
        print(
            f"  Registration Token: {decoded_details.get('registration_token', 'N/A')}"
        )
        print(f"  Expiration: {decoded_details.get('__expired__', 'Active')}")
        print()


def main():
    """Main monitoring function."""
    print("\n" + "=" * 50)
    print("SYNTHIA API - SYSTEM MONITOR")
    print("=" * 50)

    monitor_jobs()
    monitor_users()


if __name__ == "__main__":
    main()
