"""
Database connection and initialization for S.H.I.E.L.D.

Manages database connections, sessions, and initialization.
"""

from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import sqlite3
import logging

from shield.database.models import Base
from shield.core.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """
    Manages database connections and sessions.
    
    Features:
    - Connection pooling
    - Session management
    - Transaction handling
    - Automatic initialization
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        connection_string = f"sqlite:///{self.db_path}"
        
        # Enable foreign keys and connection pooling
        self.engine = create_engine(
            connection_string,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        
        # Enable foreign key constraints
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        
        logger.info(f"Database connection initialized: {self.db_path}")
    
    def initialize(self) -> bool:
        """
        Initialize database schema.
        
        Creates all tables if they don't exist.
        
        Returns:
            True if successful
        """
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database schema initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {str(e)}")
            return False
    
    def get_session(self) -> Session:
        """
        Get a database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()
    
    def close(self) -> None:
        """Close database connection"""
        self.engine.dispose()
        logger.info("Database connection closed")
    
    def health_check(self) -> bool:
        """
        Check database health.
        
        Returns:
            True if database is accessible
        """
        try:
            session = self.get_session()
            session.execute("SELECT 1")
            session.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


# Global database connection
_db_connection: DatabaseConnection = None


def initialize_database(db_path: Path = None) -> DatabaseConnection:
    """
    Initialize the global database connection.
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        DatabaseConnection instance
    """
    global _db_connection
    
    if db_path is None:
        from shield.core.config import Config
        config = Config.get()
        db_path = config.memory.sqlite_db_path
    
    if isinstance(db_path, str):
        db_path = Path(db_path).expanduser()
    
    _db_connection = DatabaseConnection(db_path)
    _db_connection.initialize()
    
    return _db_connection


def get_database() -> DatabaseConnection:
    """
    Get the global database connection.
    
    Returns:
        DatabaseConnection instance
    
    Raises:
        RuntimeError: If database not initialized
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = initialize_database()
    return _db_connection


def get_db_session() -> Session:
    """
    Get a database session.
    
    Returns:
        SQLAlchemy session
    """
    db = get_database()
    return db.get_session()


# Context manager for database sessions
class SessionContext:
    """Context manager for database sessions"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self) -> Session:
        self.session = get_db_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
