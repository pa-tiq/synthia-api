from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config.settings import CORS_ORIGINS
from app.api.endpoints import summarize
from app.utils.temp_manager import setup_periodic_cleanup, startup_cleanup

app = FastAPI(
    title="Synthia API", description="API for summarizing various types of files"
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


# Register startup events
@app.on_event("startup")
async def startup_event():
    await startup_cleanup()
    await setup_periodic_cleanup()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
