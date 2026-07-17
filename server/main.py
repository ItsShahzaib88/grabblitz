"""
SaveFlow — FastAPI Backend Entry Point
Production-ready server with CORS, rate limiting, and structured error handling.
"""
import sys
import os
import asyncio

# Ensure the server directory is in sys.path for module resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Windows Fix: asyncio subprocess requires ProactorEventLoop ---
# SelectorEventLoop (default on Windows) does NOT support subprocesses.
# This MUST be set before uvicorn/FastAPI starts the event loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from api.routes import router
from utils.rate_limiter import rate_limiter


# --- Lifespan (startup/shutdown) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — background cleanup task."""
    # Start periodic cleanup of rate limiter
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


async def periodic_cleanup():
    """Run rate limiter cleanup every 5 minutes."""
    while True:
        await asyncio.sleep(300)
        rate_limiter.cleanup()


# --- App Factory ---

app = FastAPI(
    title="SaveFlow API",
    description="Production-ready media downloader API supporting 30+ platforms.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# --- CORS ---
# In production, replace "*" with your frontend domain(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


# --- Global Exception Handler ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "server_error", "message": "An unexpected error occurred."},
    )


# --- Mount API Routes ---

app.include_router(router, prefix="/api")


# --- Root Redirect ---

@app.get("/")
async def root():
    return {"message": "SaveFlow API is running. See /api/docs for documentation."}


# --- Entry Point ---

if __name__ == "__main__":
    import uvicorn
    
    # Render provides a PORT environment variable, usually 10000. 
    # If not found, default to 8000 for local development.
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Should be False in production
        log_level="info",
        loop="asyncio",   # Uses ProactorEventLoop on Windows (set above)
    )
