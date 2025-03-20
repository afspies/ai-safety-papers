from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from pathlib import Path

from backend.src.api.routers import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get root directory
project_root = Path(__file__).parent.parent.parent.parent
static_dir = project_root / "ai-safety-site" / "content" / "en" / "posts"
logger.info(f"Static directory: {static_dir}")

# Initialize FastAPI app
app = FastAPI(
    title="AI Safety Papers API",
    description="Backend API for AI Safety Papers project",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router, prefix="/api")

# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    logger.warning(f"Static directory does not exist: {static_dir}")

@app.get("/")
async def root():
    """Root endpoint returning API info."""
    return {
        "message": "Welcome to the AI Safety Papers API",
        "version": "1.0.0",
        "endpoints": {
            "papers": "/api/papers",
            "paper_detail": "/api/papers/{paper_id}",
            "highlighted_papers": "/api/papers/highlighted"
        }
    }

def start():
    """Start the FastAPI server using uvicorn."""
    uvicorn.run(
        "backend.src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

if __name__ == "__main__":
    start()