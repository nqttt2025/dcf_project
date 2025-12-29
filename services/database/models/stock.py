"""
Stock model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    exchange = Column(String(20), default="HOSE")
    is_vn30 = Column(Boolean, default=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    last_sync_date = Column(DateTime(timezone=True))
    sync_status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

