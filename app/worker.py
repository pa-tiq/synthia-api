# app/worker.py
import redis
from rq import Worker

listen = ["default"]

redis_url = "redis://localhost:6379"

conn = redis.from_url(redis_url)

if __name__ == "__main__":
    worker = Worker(listen, connection=conn)
    worker.work()
