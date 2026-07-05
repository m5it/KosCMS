"""
Pytest Configuration
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from webcms.models.base import Base


@pytest.fixture
def db_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()