"""
Database initialization and management
"""
import os
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from bot.config import DATABASE_URL
from bot.models import Base

logger = logging.getLogger(__name__)

# Database engine and session
engine = None
SessionLocal = None

def init_database():
    """Initialize database connection and create tables"""
    global engine, SessionLocal
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        
        # Test database connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Fallback to file-based storage if database fails
        init_file_storage()

def get_db():
    """Get database session"""
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        yield None

def init_file_storage():
    """Initialize file-based storage as fallback"""
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize JSON files if they don't exist
    files = {
        "channels.json": [],
        "admins.json": [],
        "keywords.json": [],
        "welcome_messages.json": {}
    }
    
    for filename, default_content in files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump(default_content, f, indent=2)
    
    logger.info("File-based storage initialized")

def load_json_data(filename):
    """Load data from JSON file"""
    try:
        filepath = os.path.join("data", filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        return [] if filename != "welcome_messages.json" else {}

def save_json_data(filename, data):
    """Save data to JSON file"""
    try:
        filepath = os.path.join("data", filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        return False
