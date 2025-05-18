from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api import auth, search, chat
from app.services.code_search import code_search_service

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and load models"""
    await connect_to_mongo()
    # Initialize the code search service in the background
    # This will load models and embeddings
    await code_search_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    await close_mongo_connection()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Code Search API",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)