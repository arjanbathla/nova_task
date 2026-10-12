import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, Application


def get_engine(database_url: str):
    """Create and return a SQLAlchemy engine."""
    return create_engine(database_url, connect_args={"check_same_thread": False})


def init_db(engine):
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


# Create a global sessionmaker cache to ensure session consistency
_sessionmakers = {}


def get_session(engine) -> Session:
    """Create and return a new database session."""
    # Use the same sessionmaker for the same engine to ensure connection pooling works
    engine_id = id(engine)
    if engine_id not in _sessionmakers:
        _sessionmakers[engine_id] = sessionmaker(bind=engine)
    return _sessionmakers[engine_id]()


def save_application(session: Session, application_data: dict) -> Application:
    """
    Save an application to the database.
    
    Args:
        session: SQLAlchemy session
        application_data: Dict with keys: id, name, age, smoker, coverage_amount,
                         occupation, pre_existing_conditions, status, quote, 
                         breakdown (dict), reason, created_at
    
    Returns:
        Saved Application object
    """
    # Serialize breakdown dict to JSON string
    data = application_data.copy()
    data["breakdown"] = json.dumps(data["breakdown"])
    
    application = Application(**data)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def get_application_by_id(session: Session, application_id: str) -> Application | None:
    """
    Retrieve an application by ID.
    
    Args:
        session: SQLAlchemy session
        application_id: UUID string
    
    Returns:
        Application object or None if not found
    """
    return session.query(Application).filter_by(id=application_id).first()
