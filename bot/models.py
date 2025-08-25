"""
Database models for the bot
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    added_by = Column(BigInteger, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(BigInteger, unique=True, index=True, nullable=False)
    channel_name = Column(String(255), nullable=True)
    channel_username = Column(String(255), nullable=True)
    added_by = Column(BigInteger, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    member_count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, index=True, nullable=False)
    added_by = Column(BigInteger, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    detection_count = Column(Integer, default=0)

class WelcomeMessage(Base):
    __tablename__ = "welcome_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, index=True, nullable=False)
    message = Column(Text, nullable=False)
    set_by = Column(BigInteger, nullable=False)
    set_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class BotStats(Base):
    __tablename__ = "bot_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    total_users = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    filtered_messages = Column(Integer, default=0)
    active_channels = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
