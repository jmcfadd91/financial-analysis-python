"""SQLAlchemy ORM models for persistent storage."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class PositionModel(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True)
    ticker = Column(String(20), nullable=False)
    shares = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_date = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WatchlistModel(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, unique=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NotificationConfigModel(Base):
    __tablename__ = "notification_config"

    id = Column(Integer, primary_key=True, default=1)
    bot_token = Column(Text, nullable=False, default="")
    chat_id = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
