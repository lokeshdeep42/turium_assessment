import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple
from logger import logger

class ContentIngestion:
    """Handles content ingestion from notes and URLs."""
    
    @staticmethod
    def extract_url_content(url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Extract text content from a URL.
        
        Returns:
            Tuple of (success, content, error_message)
        """
        try:
            # Set headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Fetch the URL with timeout
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            if not text:
                return False, "", "No text content found at URL"
            
            logger.info(f"Successfully extracted {len(text)} characters from {url}")
            return True, text, None
            
        except requests.Timeout:
            error = "Request timed out"
            logger.error(f"Timeout fetching {url}")
            return False, "", error
            
        except requests.RequestException as e:
            error = f"Failed to fetch URL: {str(e)}"
            logger.error(f"Error fetching {url}: {e}")
            return False, "", error
            
        except Exception as e:
            error = f"Error parsing content: {str(e)}"
            logger.error(f"Error parsing {url}: {e}")
            return False, "", error
    
    @staticmethod
    def validate_note(content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate note content.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content or not content.strip():
            return False, "Note content cannot be empty"
        
        if len(content) > 50000:  # 50k character limit
            return False, "Note content too long (max 50,000 characters)"
        
        return True, None
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            chunk_size: Number of words per chunk
            overlap: Number of words to overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Simple word-based chunking
        words = text.split()
        chunks = []
        
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


# Global ingestion instance
content_ingestion = ContentIngestion()

async def process_content(content: str, source_type: str) -> int:
    """
    Process and ingest content into the knowledge base.
    
    Args:
        content: The content to ingest (note text or URL)
        source_type: Type of content ('note' or 'url')
    
    Returns:
        item_id: ID of the created item
    """
    from database import db
    from vector_store import vector_store
    
    # Extract/validate content based on type
    if source_type == "url":
        success, extracted_content, error = content_ingestion.extract_url_content(content)
        if not success:
            raise ValueError(f"Failed to extract URL content: {error}")
        final_content = extracted_content
        url = content
    else:  # note
        is_valid, error = content_ingestion.validate_note(content)
        if not is_valid:
            raise ValueError(f"Invalid note content: {error}")
        final_content = content
        url = None
    
    # Insert item into database
    item_id = db.insert_item(
        content=final_content,
        source_type=source_type,
        url=url
    )
    
    # Chunk the content
    chunks = content_ingestion.chunk_text(final_content)
    logger.info(f"Split text into {len(chunks)} chunks")
    
    # Process each chunk
    for i, chunk_text in enumerate(chunks):
        # Insert chunk into database
        chunk_id = db.insert_chunk(
            item_id=item_id,
            chunk_text=chunk_text,
            chunk_index=i
        )
        
        # Add to vector store
        chunk_metadata = {
            'chunk_id': chunk_id,
            'item_id': item_id,
            'chunk_index': i
        }
        vector_store.add_chunk(chunk_text, chunk_metadata)
    
    logger.info(f"Processed {len(chunks)} chunks for item {item_id}")
    return item_id
