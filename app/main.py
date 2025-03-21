from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import CORS_ORIGINS
from app.api.endpoints import summarize
from app.utils.temp_manager import setup_periodic_cleanup, startup_cleanup
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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
