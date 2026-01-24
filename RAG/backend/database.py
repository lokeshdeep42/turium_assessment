import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from config import config
from logger import logger

class Database:
    """SQLite database manager for the knowledge inbox."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    source_type TEXT NOT NULL CHECK(source_type IN ('note', 'url')),
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chunks table for storing text chunks and their embeddings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_items_source_type 
                ON items(source_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_item_id 
                ON chunks(item_id)
            """)
            
            logger.info("Database initialized successfully")
    
    def insert_item(self, content: str, source_type: str, url: Optional[str] = None) -> int:
        """Insert a new item into the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO items (content, source_type, url) VALUES (?, ?, ?)",
                (content, source_type, url)
            )
            item_id = cursor.lastrowid
            logger.info(f"Inserted item {item_id} of type {source_type}")
            return item_id
    
    def insert_chunk(self, item_id: int, chunk_text: str, chunk_index: int) -> int:
        """Insert a text chunk for an item."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chunks (item_id, chunk_text, chunk_index) VALUES (?, ?, ?)",
                (item_id, chunk_text, chunk_index)
            )
            return cursor.lastrowid
    
    def get_all_items(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all items, optionally filtered by source type."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if source_type:
                cursor.execute(
                    "SELECT * FROM items WHERE source_type = ? ORDER BY created_at DESC",
                    (source_type,)
                )
            else:
                cursor.execute("SELECT * FROM items ORDER BY created_at DESC")
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific item by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_chunks_by_item_id(self, item_id: int) -> List[Dict[str, Any]]:
        """Retrieve all chunks for a specific item."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chunks WHERE item_id = ? ORDER BY chunk_index",
                (item_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Retrieve all chunks from all items."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, i.source_type, i.url 
                FROM chunks c
                JOIN items i ON c.item_id = i.id
                ORDER BY c.id
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_item(self, item_id: int) -> bool:
        """Delete an item and its associated chunks."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted item {item_id}")
            return deleted

# Global database instance
db = Database()
