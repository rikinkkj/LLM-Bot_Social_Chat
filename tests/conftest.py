import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Bot, Post, Memory

@pytest.fixture(scope="function")
def db_session():
    """
    Creates a new, in-memory SQLite database session for each test function.
    This ensures that tests are isolated and don't interfere with each other.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()
