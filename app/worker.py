import os
import sys

# Add the project's root directory to the PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import redis
from rq import Worker

listen = ["default"]

redis_url = "redis://localhost:6379"

conn = redis.from_url(redis_url)

if __name__ == "__main__":
    worker = Worker(listen, connection=conn)
    worker.work()
