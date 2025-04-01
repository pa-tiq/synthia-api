from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import CORS_ORIGINS
from app.api.endpoints import summarize
from app.api.endpoints import auth
from app.utils.temp_manager import setup_periodic_cleanup, startup_cleanup
from app.utils.rate_limiter import RateLimiter
import redis
from rq import Queue

# Initialize Redis and RQ
redis_conn = redis.Redis()
queue = Queue(connection=redis_conn)


# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await startup_cleanup()
    cleanup_task = await setup_periodic_cleanup()

    # Store Redis queue in app state
    app.state.redis_queue = queue

    yield  # This is where the app runs

    # Shutdown code (if you have any)
    cleanup_task.cancel()  # Cancel the periodic task if it returns a task


# Create the FastAPI app with lifespan
app = FastAPI(
    title="Synthia API",
    description="API for summarizing various types of files",
    lifespan=lifespan,
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    rate_limiter = RateLimiter(requests_per_minute=90)
    await rate_limiter(request)
    response = await call_next(request)
    return response


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(summarize.router, tags=["summarization"])
app.include_router(auth.router, tags=["authentication"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Store Redis connection in app state
app.state.redis_conn = redis_conn
app.state.redis_queue = queue
