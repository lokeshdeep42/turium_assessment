from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from models import IngestRequest, IngestResponse, Item, QueryRequest, QueryResponse, SourceSnippet
from database import db
from ingestion import process_content
from rag_pipeline import rag_pipeline
from logger import logger

router = APIRouter(prefix="/api", tags=["api"])

@router.post("/ingest", response_model=IngestResponse)
async def ingest_content(request: IngestRequest):
    """
    Ingest content (note or URL) into the knowledge base.
    """
    try:
        content = request.content
        source_type = request.source_type
        
        # Validate source type
        if source_type not in ["note", "url"]:
            raise HTTPException(status_code=400, detail="source_type must be 'note' or 'url'")
        
        # Process the content
        item_id = await process_content(content, source_type)
        
        logger.info(f"Successfully ingested {source_type} with ID {item_id}")
        
        return IngestResponse(
            success=True,
            message=f"Successfully ingested {source_type}",
            item_id=item_id
        )
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items", response_model=List[Item])
async def get_items(source_type: Optional[str] = Query(None, regex="^(note|url)$")):
    """
    Retrieve all saved items, optionally filtered by type.
    """
    try:
        items = db.get_all_items(source_type)
        logger.info(f"Retrieved {len(items)} items (filter: {source_type})")
        return items
        
    except Exception as e:
        logger.error(f"Error retrieving items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """
    Retrieve a specific item by ID.
    """
    try:
        item = db.get_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        
        logger.info(f"Retrieved item {item_id}")
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """
    Delete an item and its associated chunks from the database.
    """
    try:
        # Check if item exists
        item = db.get_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        
        # Delete the item (cascades to chunks)
        success = db.delete_item(item_id)
        
        if success:
            logger.info(f"Deleted item {item_id}")
            return {
                "success": True,
                "message": f"Item {item_id} deleted successfully",
                "item_id": item_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete item")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Query the knowledge base with a question.
    """
    try:
        question = request.question
        max_results = request.max_results or 5
        
        # Query the RAG pipeline
        answer, sources = rag_pipeline.query(question, max_results)
        
        # Convert sources to response model
        source_snippets = [
            SourceSnippet(**source) for source in sources
        ]
        
        logger.info(f"Answered query with {len(source_snippets)} sources")
        
        return QueryResponse(
            answer=answer,
            sources=source_snippets,
            question=question
        )
        
    except Exception as e:
        logger.error(f"Error during query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    from vector_store import vector_store
    
    return {
        "status": "healthy",
        "items_count": len(db.get_all_items()),
        "vector_store_size": vector_store.size()
    }
