"""
 * Grid SQLAlchemy model.
"""
import uuid
import datetime
from sqlalchemy import Column, String, Integer, DateTime
from app.infrastructure.db import Base


class Grid(Base):
    __tablename__ = "grids"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bbox = Column(String, nullable=False)
    grid_size_m = Column(Integer, nullable=False)
    num_cells = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="loading")