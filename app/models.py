from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    smoker = Column(Boolean, nullable=False)
    coverage_amount = Column(Integer, nullable=False)
    occupation = Column(String(20), nullable=False)
    pre_existing_conditions = Column(Boolean, nullable=False)
    status = Column(String(20), nullable=False)
    quote = Column(Float, nullable=True)
    breakdown = Column(Text, nullable=False)
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
