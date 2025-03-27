# This could be used to collect all routers for easier inclusion in main.py
from app.api.endpoints.summarize import router as summarize_router
from app.api.endpoints.security import router as security_router

routers = [summarize_router, security_router]
