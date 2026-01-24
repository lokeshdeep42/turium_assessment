from openai import AzureOpenAI
from typing import List, Dict, Any, Tuple
from config import config
from logger import logger
from database import db
from vector_store import vector_store

class RAGPipeline:
    """RAG pipeline for chunking, embedding, and question answering."""
    
    def __init__(self):
        if config.AZURE_OPENAI_API_KEY and config.AZURE_OPENAI_ENDPOINT:
            self.client = AzureOpenAI(
                api_key=config.AZURE_OPENAI_API_KEY,
                api_version=config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT
            )
            logger.info("Azure OpenAI client configured for RAG pipeline")
        else:
            self.client = None
            logger.warning("Azure OpenAI credentials not set")
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Uses a simple token-based approach with fixed size and overlap.
        """
        # Simple word-based chunking (approximates tokens)
        words = text.split()
        chunks = []
        
        chunk_size = config.CHUNK_SIZE
        overlap = config.CHUNK_OVERLAP
        
        if len(words) <= chunk_size:
            return [text]
        
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            
            # Prevent infinite loop
            if start >= len(words):
                break
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def process_and_store_content(self, item_id: int, content: str) -> bool:
        """
        Process content: chunk it, generate embeddings, and store in vector store.
        """
        try:
            # Chunk the content
            chunks = self.chunk_text(content)
            
            # Store each chunk
            for idx, chunk_text in enumerate(chunks):
                # Save chunk to database
                chunk_id = db.insert_chunk(item_id, chunk_text, idx)
                
                # Add to vector store with metadata
                chunk_metadata = {
                    'chunk_id': chunk_id,
                    'item_id': item_id,
                    'chunk_index': idx
                }
                vector_store.add_chunk(chunk_text, chunk_metadata)
            
            logger.info(f"Processed {len(chunks)} chunks for item {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing content for item {item_id}: {e}")
            return False
    
    def generate_answer(self, question: str, context_chunks: List[Tuple[Dict[str, Any], float]]) -> str:
        """
        Generate an answer using Azure OpenAI with retrieved context.
        """
        try:
            if not self.client:
                raise ValueError("Azure OpenAI client not configured")
            
            # Build context from chunks
            context_parts = []
            for chunk_data, score in context_chunks:
                chunk_text = chunk_data['text']
                context_parts.append(f"[Relevance: {score:.2f}] {chunk_text}")
            
            context = "\n\n".join(context_parts)
            
            # Create messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant answering questions based on the user's saved knowledge base. Answer questions based ONLY on the provided context. If the context doesn't contain enough information, say so. Be concise and accurate."
                },
                {
                    "role": "user",
                    "content": f"""Context from knowledge base:
{context}

Question: {question}

Please answer the question based on the context above. Cite which parts of the context you used."""
                }
            ]
            
            # Generate response using Azure OpenAI
            response = self.client.chat.completions.create(
                model=config.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=messages,
                temperature=config.TEMPERATURE,
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Generated answer for question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
    
    def query(self, question: str, max_results: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Query the knowledge base and generate an answer.
        
        Returns:
            Tuple of (answer, source_snippets)
        """
        try:
            # Search vector store
            search_results = vector_store.search(question, top_k=max_results)
            
            if not search_results:
                return "I don't have any relevant information to answer this question.", []
            
            # Generate answer
            answer = self.generate_answer(question, search_results)
            
            # Prepare source snippets
            sources = []
            seen_items = set()
            
            for chunk_data, score in search_results:
                item_id = chunk_data['metadata']['item_id']
                
                # Avoid duplicate items in sources
                if item_id in seen_items:
                    continue
                seen_items.add(item_id)
                
                # Get item details from database
                item = db.get_item_by_id(item_id)
                if item:
                    sources.append({
                        'item_id': item_id,
                        'content': chunk_data['text'][:200] + "..." if len(chunk_data['text']) > 200 else chunk_data['text'],
                        'source_type': item['source_type'],
                        'url': item.get('url'),
                        'relevance_score': float(score)
                    })
            
            return answer, sources
            
        except Exception as e:
            logger.error(f"Error during query: {e}")
            raise

# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
