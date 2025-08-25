# Overview

This is a comprehensive Telegram bot designed for channel management with advanced features including AI-powered copyright protection, movie search capabilities, and multi-admin management system. The bot serves as a complete channel management solution with web-based admin panel, automated content filtering, and integration with The Movie Database (TMDB) API for movie search functionality.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework and Communication
- **Telegram Bot API**: Core communication layer using python-telegram-bot library with async/await patterns
- **Command Handlers**: Modular command system with separate handlers for different functionalities (admin, channel management, movie search, copyright filtering)
- **Callback Query System**: Interactive inline keyboards for user-friendly navigation and actions
- **Webhook Support**: Designed to handle both polling and webhook modes for Telegram updates

## Data Storage and Persistence
- **Hybrid Storage System**: SQLAlchemy ORM with fallback to JSON file storage for resilience
- **Database Models**: Structured entities for Admins, Channels, Keywords, Welcome Messages, and Bot Statistics
- **File-based Backup**: JSON files in `/data` directory serve as backup and fallback storage
- **Database Abstraction**: Clean separation between database operations and business logic

## Web Interface and Monitoring
- **Flask Web Server**: Administrative web panel for bot management and monitoring
- **Health Monitoring**: Real-time system health checks with uptime tracking and resource monitoring
- **Admin Dashboard**: Web-based interface for managing admins, channels, and viewing statistics
- **Static Assets**: CSS and JavaScript for responsive web interface

## AI-Powered Content Filtering
- **Copyright Protection**: AI-based content analysis using NLTK, TextBlob, and scikit-learn
- **Keyword Detection**: Configurable keyword filtering system with pattern matching
- **Content Analysis**: TF-IDF vectorization and cosine similarity for content comparison
- **Graceful Degradation**: Falls back to keyword-based filtering when AI libraries unavailable

## Administrative System
- **Multi-tier Admin System**: Super admins and regular admins with different privilege levels
- **Role-based Access Control**: Hierarchical permission system for different administrative functions
- **Admin Management**: Complete CRUD operations for admin users with audit trails
- **Channel Management**: Add, remove, and monitor multiple Telegram channels

## Movie Search Integration
- **TMDB API Integration**: The Movie Database API for comprehensive movie information
- **Search Functionality**: Advanced movie search with detailed information display
- **Error Handling**: Robust error handling for API failures and rate limiting
- **Response Formatting**: Rich message formatting with movie details and poster images

## Configuration and Environment
- **Environment-based Configuration**: All sensitive data managed through environment variables
- **Feature Toggles**: AI features can be enabled/disabled based on environment configuration
- **Threshold Management**: Configurable sensitivity levels for copyright detection
- **Logging System**: Comprehensive logging with file and console output

# External Dependencies

## Core Infrastructure
- **Telegram Bot API**: Primary communication channel for bot interactions
- **Python Telegram Bot Library**: Async framework for Telegram bot development
- **SQLAlchemy**: Database ORM with support for multiple database backends
- **Flask**: Web framework for admin panel and health monitoring endpoints

## AI and Machine Learning
- **NLTK**: Natural Language Toolkit for text preprocessing and analysis
- **TextBlob**: Sentiment analysis and text processing capabilities
- **scikit-learn**: Machine learning tools for TF-IDF vectorization and similarity analysis
- **psutil**: System monitoring and resource usage tracking

## Movie Data Service
- **TMDB (The Movie Database) API**: Movie information, search, and metadata retrieval
- **Requests Library**: HTTP client for API communications with timeout and error handling

## System Monitoring
- **psutil**: Cross-platform system and process monitoring
- **datetime**: Time tracking for uptime calculations and scheduling
- **platform**: System information gathering for health monitoring

## Development and Deployment
- **python-dotenv**: Environment variable management for development
- **aiohttp**: Async HTTP server for webhook handling and health checks
- **logging**: Comprehensive logging system with multiple output handlers