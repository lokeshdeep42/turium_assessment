from openai import AzureOpenAI
from typing import List, Tuple, Dict, Any
from config import config
from logger import logger

class VectorStore:
    """Simple in-memory vector store using cosine similarity for search."""
    
    def __init__(self):
        self.embeddings: List[List[float]] = []
        self.chunks: List[Dict[str, Any]] = []
        self.dimension: int = config.EMBEDDING_DIMENSION  # Azure text-embedding-ada-002: 1536
        
        # Configure Azure OpenAI client
        if config.AZURE_OPENAI_API_KEY and config.AZURE_OPENAI_ENDPOINT:
            self.client = AzureOpenAI(
                api_key=config.AZURE_OPENAI_API_KEY,
                api_version=config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT
            )
            logger.info("Azure OpenAI client configured successfully")
        else:
            self.client = None
            logger.warning("Azure OpenAI credentials not set - embeddings will fail")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Azure OpenAI."""
        try:
            if not self.client:
                raise ValueError("Azure OpenAI client not configured")
            
            response = self.client.embeddings.create(
                input=text,
                model=config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with dimension {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a query using Azure OpenAI."""
        # For Azure OpenAI, query and document embeddings use the same method
        return self.generate_embedding(query)
    
    def add_chunk(self, chunk_text: str, chunk_metadata: Dict[str, Any]):
        """Add a chunk and its embedding to the vector store."""
        try:
            embedding = self.generate_embedding(chunk_text)
            self.embeddings.append(embedding)
            self.chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })
            logger.info(f"Added chunk {chunk_metadata.get('chunk_id')} to vector store")
        except Exception as e:
            logger.error(f"Error adding chunk to vector store: {e}")
            raise
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Search for most similar chunks to the query."""
        if not self.embeddings:
            logger.warning("Vector store is empty")
            return []
        
        try:
            query_embedding = self.generate_query_embedding(query)
            
            # Calculate similarities
            similarities = []
            for idx, chunk_embedding in enumerate(self.embeddings):
                similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                similarities.append((idx, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Get top k results
            top_results = similarities[:top_k]
            
            results = []
            for idx, score in top_results:
                results.append((self.chunks[idx], score))
            
            logger.info(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise
    
    def clear(self):
        """Clear all embeddings and chunks from the store."""
        self.embeddings = []
        self.chunks = []
        logger.info("Vector store cleared")
    
    def size(self) -> int:
        """Return the number of chunks in the store."""
        return len(self.chunks)
    
    def reload_from_database(self, db):
        """Reload all chunks from database and regenerate embeddings."""
        try:
            logger.info("Reloading vector store from database...")
            
            # Get all chunks from database
            all_chunks = db.get_all_chunks()
            
            if not all_chunks:
                logger.info("No chunks found in database")
                return
            
            # Clear existing data
            self.clear()
            
            # Regenerate embeddings for each chunk
            for chunk in all_chunks:
                chunk_metadata = {
                    'chunk_id': chunk['id'],
                    'item_id': chunk['item_id'],
                    'chunk_index': chunk['chunk_index']
                }
                
                # Add chunk with its embedding
                self.add_chunk(chunk['chunk_text'], chunk_metadata)
            
            logger.info(f"Reloaded {len(all_chunks)} chunks into vector store")
            
        except Exception as e:
            logger.error(f"Error reloading vector store from database: {e}")
            raise

# Global vector store instance
vector_store = VectorStore()
