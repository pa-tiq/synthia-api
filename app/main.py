from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config.settings import CORS_ORIGINS
from app.api.endpoints import summarize
from app.utils.temp_manager import setup_periodic_cleanup, startup_cleanup


# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await startup_cleanup()
    cleanup_task = await setup_periodic_cleanup()

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


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
