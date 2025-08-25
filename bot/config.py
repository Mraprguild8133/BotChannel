"""
Bot configuration and environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "default_tmdb_key")

# Contact Information
CONTACT_INFO = {
    'telegram': '@Sathishkumar33',
    'developer': 'Sathish Kumar'
}

# Channel Information
MOVIE_SEARCH_CHANNEL = 'https://t.me/mraprmoviesrequest'
MOVIE_DOWNLOAD_CHANNEL = 'https://t.me/mraprguildofficialmovies'

# External Services
SHORTENER_URL = 'https://www.mraprguilds.site'
GITHUB_URL = 'https://github.com/Mraprguild'

# API Keys
SHORTENER_API_KEY = os.getenv('SHORTENER_API_KEY', '')

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

# Admin configuration
SUPER_ADMINS = [int(x) for x in os.getenv("SUPER_ADMINS", "").split(",") if x.strip()]

# Copyright filter configuration
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"
COPYRIGHT_THRESHOLD = float(os.getenv("COPYRIGHT_THRESHOLD", "0.7"))

# Channel configuration
MAX_CHANNELS_PER_ADMIN = int(os.getenv("MAX_CHANNELS_PER_ADMIN", "10"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
