from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import CORS_ORIGINS
from app.api.endpoints import summarize
from app.api.endpoints import security
from app.utils.temp_manager import setup_periodic_cleanup, startup_cleanup
import redis.asyncio as redis
from rq import Queue
from app.api.endpoints.security import (
    AsyncRedisTokenManager,
    AsymmetricEncryptionManager,
)


# Initialize async Redis connection
async def get_redis_connection():
    """Create an async Redis connection."""
    return await redis.from_url("redis://localhost:6379")


# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await startup_cleanup()
    cleanup_task = await setup_periodic_cleanup()

    # Initialize Redis connection
    app.state.redis_client = await get_redis_connection()

    # Initialize Redis queue
    queue = Queue(connection=app.state.redis_client)
    app.state.redis_queue = queue

    # Setup security dependencies
    # Store Redis URL for security module to use
    app.state.redis_url = "redis://localhost:6379"

    # Import and call setup function from security module
    from app.api.endpoints.security import setup_security_dependencies

    setup_security_dependencies(app)

    yield  # This is where the app runs

    # Shutdown code
    cleanup_task.cancel()  # Cancel the periodic task
    await app.state.redis_client.close()


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
app.include_router(security.router, prefix="/security", tags=["security"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
