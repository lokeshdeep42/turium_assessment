from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from logger import logger

app = FastAPI(
    title="AI Knowledge Inbox",
    description="A minimal RAG-powered knowledge management system",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Knowledge Inbox API")
    
    # Reload vector store from database
    try:
        from database import db
        from vector_store import vector_store
        vector_store.reload_from_database(db)
    except Exception as e:
        logger.error(f"Failed to reload vector store: {e}")
        # Don't fail startup, just log the error


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Knowledge Inbox API")

@app.get("/")
async def root():
    return {
        "message": "AI Knowledge Inbox API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
