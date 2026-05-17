"""Main FastAPI application"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.api import auth, organizations, meetings, graph, segmentation, extraction, execution
from app.api.intelligence import router as intelligence_router
from app.realtime.websocket import ws_router
from app.realtime.intelligence_ws import intelligence_ws_router
from app.ai_pipeline.queue import ai_queue
# Import models to register them with Base metadata
from app.models import *  # noqa: F401, F403

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    await init_db()
    await ai_queue.init()
    print("✓ Database initialized")
    print("✓ Redis connection established")
    
    yield
    
    # Shutdown
    await close_db()
    await ai_queue.close()
    print("✓ Graceful shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Meeting Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(meetings.router)
app.include_router(graph.router)
app.include_router(segmentation.router)
app.include_router(extraction.router)
app.include_router(execution.router)
app.include_router(intelligence_router)
app.include_router(ws_router)
app.include_router(intelligence_ws_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
    }


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
