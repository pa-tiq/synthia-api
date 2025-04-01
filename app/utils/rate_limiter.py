from fastapi import FastAPI, Request, HTTPException
import time
from redis import Redis

# Initialize Redis client
redis_client = Redis(host="localhost", port=6379, db=0)


class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute in seconds

    async def __call__(self, request: Request):
        # Get the device ID from the JWT token
        if not hasattr(request.state, "device_id"):
            # If we're in an endpoint that doesn't require authentication,
            # use the IP address instead
            identifier = request.client.host
        else:
            identifier = request.state.device_id

        # Create a Redis key for this user's rate limit
        key = f"rate_limit:{identifier}"

        # Get current count
        current = redis_client.get(key)
        current = int(current) if current else 0

        if current >= self.requests_per_minute:
            raise HTTPException(
                status_code=429, detail="Too many requests. Please try again later."
            )

        # Increment count and set expiry if it doesn't exist
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window_size)
        pipe.execute()
