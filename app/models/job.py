"""
 * Job SQLAlchemy model.
"""
import uuid
import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from app.infrastructure.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    grid_id = Column(String, ForeignKey("grids.id"), nullable=True)
    status = Column(String, default="pending")
    progress = Column(Float, default=0.0)
    step = Column(String, default="")
    result_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)