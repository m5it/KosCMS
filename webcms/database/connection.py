"""
Database Connection Manager

SQLAlchemy with connection pooling and session management.
"""

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from webcms.models.base import Base


class DatabaseManager:
    """Database connection manager with pooling."""
    
    def __init__(self, database_url: str, pool_size: int = 10, 
                 max_overflow: int = 20, echo: bool = False):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
        self._setup_engine(pool_size, max_overflow, echo)
    
    def _setup_engine(self, pool_size: int, max_overflow: int, echo: bool):
        """Create database engine with connection pooling."""
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=echo
        )
        
        # Add connection event listeners
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            """Set connection pragmas for SQLite."""
            if self.database_url.startswith("sqlite"):
                dbapi_conn.execute("PRAGMA foreign_keys=ON")
                dbapi_conn.execute("PRAGMA journal_mode=WAL")
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide transactional scope around operations."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """Close all connections."""
        if self.engine:
            self.engine.dispose()


# Global instance
_db_manager: Optional[DatabaseManager] = None


def init_db(database_url: str, **kwargs) -> DatabaseManager:
    """Initialize database."""
    global _db_manager
    _db_manager = DatabaseManager(database_url, **kwargs)
    _db_manager.create_tables()
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized")
    
    db = _db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


def get_db_manager() -> DatabaseManager:
    """Get database manager instance."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized")
    return _db_manager