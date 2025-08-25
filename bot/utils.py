"""
Utility functions for the bot
"""
import logging
import json
import os
from typing import Dict, Any, Optional
from bot.database import load_json_data
from bot.config import SUPER_ADMINS

logger = logging.getLogger(__name__)

async def is_admin(user_id: int) -> bool:
    """Check if user is an admin"""
    # Check super admins first
    if user_id in SUPER_ADMINS:
        return True
    
    # Check database/file admins
    try:
        admins = load_json_data("admins.json")
        return any(
            admin['user_id'] == user_id and admin.get('is_active', True)
            for admin in admins
        )
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def is_super_admin(user_id: int) -> bool:
    """Check if user is a super admin"""
    return user_id in SUPER_ADMINS

def get_user_info(user) -> Dict[str, Any]:
    """Extract user information from Telegram user object"""
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "language_code": user.language_code,
        "is_bot": user.is_bot
    }

def get_chat_info(chat) -> Dict[str, Any]:
    """Extract chat information from Telegram chat object"""
    return {
        "id": chat.id,
        "type": chat.type,
        "title": getattr(chat, 'title', None),
        "username": getattr(chat, 'username', None),
        "description": getattr(chat, 'description', None)
    }

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and dots
    sanitized = re.sub(r'[.\s]+', '_', sanitized)
    # Limit length
    return sanitized[:100]

def validate_url(url: str) -> bool:
    """Validate if string is a valid URL"""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def parse_channel_input(channel_input: str) -> Dict[str, Optional[str]]:
    """Parse channel input and return channel ID and username"""
    result = {"id": None, "username": None}
    
    if channel_input.startswith('@'):
        result["username"] = channel_input[1:]
    elif channel_input.startswith('https://t.me/'):
        result["username"] = channel_input.split('/')[-1]
    else:
        try:
            result["id"] = int(channel_input)
        except ValueError:
            pass
    
    return result

def get_bot_stats() -> Dict[str, Any]:
    """Get bot statistics"""
    try:
        # Load data
        admins = load_json_data("admins.json")
        channels = load_json_data("channels.json")
        keywords = load_json_data("keywords.json")
        welcome_messages = load_json_data("welcome_messages.json")
        
        # Calculate stats
        stats = {
            "total_admins": len([a for a in admins if a.get('is_active', True)]),
            "total_channels": len([c for c in channels if c.get('is_active', True)]),
            "total_keywords": len([k for k in keywords if k.get('is_active', True)]),
            "total_welcome_messages": len(welcome_messages),
            "total_members": sum(c.get('member_count', 0) for c in channels if c.get('is_active', True)),
            "avg_members_per_channel": 0
        }
        
        if stats["total_channels"] > 0:
            stats["avg_members_per_channel"] = stats["total_members"] / stats["total_channels"]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting bot stats: {e}")
        return {
            "total_admins": 0,
            "total_channels": 0,
            "total_keywords": 0,
            "total_welcome_messages": 0,
            "total_members": 0,
            "avg_members_per_channel": 0
        }

def log_user_action(user_id: int, action: str, details: str = ""):
    """Log user actions for audit trail"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "details": details
        }
        
        # In a production environment, this would go to a dedicated audit log
        logger.info(f"USER_ACTION: {json.dumps(log_entry)}")
        
    except Exception as e:
        logger.error(f"Error logging user action: {e}")

def create_pagination_keyboard(items, current_page: int = 1, items_per_page: int = 10, callback_prefix: str = "page"):
    """Create pagination keyboard for large lists"""
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    except ImportError:
        return items, None, {"current_page": current_page, "total_pages": 1}
    
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_items = items[start_idx:end_idx]
    
    keyboard = []
    
    # Add navigation buttons if needed
    if total_pages > 1:
        nav_buttons = []
        
        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"{callback_prefix}_{current_page - 1}")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info")
        )
        
        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton("➡️ Next", callback_data=f"{callback_prefix}_{current_page + 1}")
            )
        
        keyboard.append(nav_buttons)
    
    return page_items, InlineKeyboardMarkup(keyboard), {"current_page": current_page, "total_pages": total_pages}
