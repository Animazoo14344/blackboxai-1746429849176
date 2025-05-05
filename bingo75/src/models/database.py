import sqlite3
from pathlib import Path
from typing import Optional
import logging

class Database:
    """Database connection manager for the Bingo system."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path (str, optional): Path to SQLite database file.
                                   If None, uses default path in data directory.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "bingo.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")
            logging.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            raise
            
    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query with parameters.
        
        Args:
            query (str): SQL query string
            params (tuple): Query parameters
            
        Returns:
            sqlite3.Cursor: Query cursor
        """
        try:
            return self.cursor.execute(query, params)
        except sqlite3.Error as e:
            logging.error(f"Query execution error: {e}\nQuery: {query}\nParams: {params}")
            raise
            
    def commit(self):
        """Commit current transaction."""
        self.conn.commit()
        
    def rollback(self):
        """Rollback current transaction."""
        self.conn.rollback()

    def create_tables(self):
        """Create all database tables."""
        queries = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0,
                totp_secret TEXT,
                failed_attempts INTEGER DEFAULT 0,
                last_failed_attempt TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Cards table
            """
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE NOT NULL,
                batch_number TEXT NOT NULL,
                numbers TEXT NOT NULL,  -- JSON array of 24 numbers (excluding FREE space)
                status TEXT CHECK(status IN ('available', 'in_play', 'won')) DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Patterns table
            """
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                grid TEXT NOT NULL,  -- JSON 5x5 grid representation
                is_moving BOOLEAN DEFAULT 0,
                movement_rules TEXT,  -- JSON movement configuration
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Games table
            """
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER NOT NULL,
                status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')) DEFAULT 'pending',
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                winner_card_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pattern_id) REFERENCES patterns(id),
                FOREIGN KEY (winner_card_id) REFERENCES cards(id)
            )
            """,
            
            # Ball calls table
            """
            CREATE TABLE IF NOT EXISTS ball_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                number INTEGER NOT NULL CHECK(number BETWEEN 1 AND 75),
                call_order INTEGER NOT NULL,
                called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id),
                UNIQUE(game_id, number),
                UNIQUE(game_id, call_order)
            )
            """,
            
            # Game cards table (cards in play for each game)
            """
            CREATE TABLE IF NOT EXISTS game_cards (
                game_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                PRIMARY KEY (game_id, card_id),
                FOREIGN KEY (game_id) REFERENCES games(id),
                FOREIGN KEY (card_id) REFERENCES cards(id)
            )
            """,
            
            # Audit log table
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        ]
        
        for query in queries:
            try:
                self.execute(query)
            except sqlite3.Error as e:
                logging.error(f"Table creation error: {e}\nQuery: {query}")
                self.rollback()
                raise
        
        self.commit()
        logging.info("Database tables created successfully")
