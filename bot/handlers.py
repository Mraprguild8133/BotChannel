"""
Basic bot command handlers for Movie Bot
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils import is_admin
from bot.database import load_json_data, save_json_data

logger = logging.getLogger(__name__)

# Configuration - Replace with your actual values
MOVIE_SEARCH_CHANNEL = "https://t.me/your_movie_search_channel"
MOVIE_DOWNLOAD_CHANNEL = "https://t.me/your_download_channel"
SHORTENER_URL = "https://your-shortener.com"
GITHUB_URL = "https://github.com/your-username/your-repo"
CONTACT_INFO = {
    'telegram': '@YourUsername',
    'email': 'your-email@example.com'
}

def get_welcome_message(chat_id=None):
    """Get current welcome message configuration"""
    welcome_data = load_json_data("welcome_messages.json")
    
    # Default welcome message if none set
    default_welcome = {
        "message": "🎬 Welcome to our movie community! Enjoy your stay and happy watching! 🍿",
        "bottom_text": "👉 Use /search to find movies or /help for more commands",
        "set_by": "system",
        "set_at": "default"
    }
    
    # Try to get chat-specific welcome message, fallback to global
    if chat_id and str(chat_id) in welcome_data:
        return welcome_data[str(chat_id)]
    elif "global" in welcome_data:
        return welcome_data["global"]
    else:
        return default_welcome

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat = update.effective_chat
    
    logger.info(f"Start command from user {user.id} in chat {chat.id}")
    
    welcome_msg = get_welcome_message(chat.id)
    
    # Create inline keyboard with useful links
    keyboard = [
        [
            InlineKeyboardButton("🎬 Movie Search", url=MOVIE_SEARCH_CHANNEL),
            InlineKeyboardButton("📥 Downloads", url=MOVIE_DOWNLOAD_CHANNEL)
        ],
        [
            InlineKeyboardButton("🌐 Website", url=SHORTENER_URL),
            InlineKeyboardButton("💻 GitHub", url=GITHUB_URL)
        ],
        [
            InlineKeyboardButton("📞 Contact", callback_data="contact"),
            InlineKeyboardButton("📋 Help", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎬 **Welcome to Movie Guild Bot!** 🍿

Hello {user.first_name}! 👋

{welcome_msg['message']}

**Our Services:**
• 🎬 Movie Search: {MOVIE_SEARCH_CHANNEL}
• 📥 Movie Downloads: {MOVIE_DOWNLOAD_CHANNEL}
• 🌐 URL Shortener: {SHORTENER_URL}
• 💻 Open Source: {GITHUB_URL}

{welcome_msg['bottom_text']}

Use /help to see all available commands!
    """
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    logger.info(f"Help command from user {user.id}")
    
    help_text = f"""
📋 **Movie Bot Commands Help** 🎬

**🔧 Basic Commands:**
/start - Start the bot and see welcome message
/help - Show this help message
/contact - Show contact information
/getid - Get your user/chat ID

**🎬 Movie Commands:**
/search <movie name> - Search for movies
/download <movie id> - Get download link
/request <movie name> - Request a movie

**👋 Welcome Messages:**
/welcome - Show current welcome message
/setwelcome <message> - Set welcome message (admin only)
/setbottomtext <text> - Set bottom text (admin only)

**👑 Admin Commands:**
/admin - Show admin panel
/addadmin <user_id> - Add new admin
/removeadmin <user_id> - Remove admin
/stats - Show bot statistics

**📺 Our Channels:**
• Movie Requests: {MOVIE_SEARCH_CHANNEL}
• Downloads: {MOVIE_DOWNLOAD_CHANNEL}
• URL Shortener: {SHORTENER_URL}

**💡 Tips:**
• Use specific movie names for better search results
• Check our channels for latest updates
• Contact support for any issues
    """
    
    keyboard = [
        [
            InlineKeyboardButton("🎬 Search Channel", url=MOVIE_SEARCH_CHANNEL),
            InlineKeyboardButton("📥 Download Channel", url=MOVIE_DOWNLOAD_CHANNEL)
        ],
        [
            InlineKeyboardButton("📞 Contact", callback_data="contact"),
            InlineKeyboardButton("🌐 Website", url=SHORTENER_URL)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text, 
        parse_mode='Markdown', 
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /contact command"""
    if not update.message:
        return
    
    contact_text = f"""
📞 **Contact Information** 👨‍💻

**Developer:** Sathish Kumar
📱 **Telegram:** {CONTACT_INFO['telegram']}
📧 **Email:** {CONTACT_INFO['email']}
🌐 **Website:** {SHORTENER_URL}
💻 **GitHub:** {GITHUB_URL}

**Our Channels:**
🎬 **Movie Requests:** {MOVIE_SEARCH_CHANNEL}
📥 **Movie Downloads:** {MOVIE_DOWNLOAD_CHANNEL}

**🆘 For Support:**
• Technical Issues: Contact via Telegram
• Movie Requests: Use our movie channel
• Bug Reports: Create GitHub issue

**🤝 Business Inquiries:**
Contact us through Telegram for partnerships and collaborations.
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📱 Contact on Telegram", url=f"https://t.me/{CONTACT_INFO['telegram'].replace('@', '')}")
        ],
        [
            InlineKeyboardButton("🎬 Movie Requests", url=MOVIE_SEARCH_CHANNEL),
            InlineKeyboardButton("📥 Downloads", url=MOVIE_DOWNLOAD_CHANNEL)
        ],
        [
            InlineKeyboardButton("🌐 Website", url=SHORTENER_URL),
            InlineKeyboardButton("💻 GitHub", url=GITHUB_URL)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        contact_text,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def get_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getid command"""
    user = update.effective_user
    chat = update.effective_chat
    
    id_text = f"""
🆔 **ID Information**

**Your User ID:** `{user.id}`
**Chat ID:** `{chat.id}`
**Chat Type:** {chat.type}

**User Info:**
• First Name: {user.first_name}
• Last Name: {user.last_name or 'N/A'}
• Username: @{user.username or 'N/A'}
• Language: {user.language_code or 'N/A'}

**Chat Info:**
• Title: {getattr(chat, 'title', 'N/A')}
• Username: @{getattr(chat, 'username', 'N/A') or 'N/A'}

Copy the IDs above for use in admin commands.
    """
    
    await update.message.reply_text(id_text, parse_mode='Markdown')

async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /welcome command - show current welcome message"""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    welcome_msg = get_welcome_message(chat_id)
    
    message = f"""
📋 **Current Welcome Configuration** 🎬

**Welcome Message:**
{welcome_msg['message']}

**Bottom Text:**
{welcome_msg['bottom_text']}

**Set by:** {welcome_msg['set_by']}
**Set at:** {welcome_msg['set_at']}

Use /setwelcome to change the welcome message (admin only)
Use /setbottomtext to change the bottom text (admin only)
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def set_welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setwelcome command"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is admin
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to use this command.")
        return
    
    # Get welcome message from command arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /setwelcome <message>\n\n"
            "Example: /setwelcome Welcome to our group! Please read the rules."
        )
        return
    
    welcome_message = " ".join(context.args)
    
    # Load and update welcome messages
    welcome_messages = load_json_data("welcome_messages.json")
    
    # Store chat-specific welcome message
    welcome_messages[str(chat.id)] = {
        "message": welcome_message,
        "bottom_text": welcome_messages.get(str(chat.id), {}).get("bottom_text", "👉 Use /search to find movies"),
        "set_by": user.id,
        "set_by_username": user.username,
        "set_at": str(update.message.date)
    }
    
    # Save updated messages
    if save_json_data("welcome_messages.json", welcome_messages):
        await update.message.reply_text(
            f"✅ Welcome message updated successfully!\n\n"
            f"**New message:**\n{welcome_message}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to save welcome message.")

async def set_bottom_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setbottomtext command"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is admin
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to use this command.")
        return
    
    # Get bottom text from command arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /setbottomtext <text>\n\n"
            "Example: /setbottomtext Check our movie channels for latest updates!"
        )
        return
    
    bottom_text = " ".join(context.args)
    
    # Load and update welcome messages
    welcome_messages = load_json_data("welcome_messages.json")
    
    # Store chat-specific bottom text
    if str(chat.id) not in welcome_messages:
        welcome_messages[str(chat.id)] = {
            "message": "🎬 Welcome to our movie community!",
            "bottom_text": bottom_text,
            "set_by": user.id,
            "set_by_username": user.username,
            "set_at": str(update.message.date)
        }
    else:
        welcome_messages[str(chat.id)]["bottom_text"] = bottom_text
        welcome_messages[str(chat.id)]["set_by"] = user.id
        welcome_messages[str(chat.id)]["set_by_username"] = user.username
        welcome_messages[str(chat.id)]["set_at"] = str(update.message.date)
    
    # Save updated messages
    if save_json_data("welcome_messages.json", welcome_messages):
        await update.message.reply_text(
            f"✅ Bottom text updated successfully!\n\n"
            f"**New bottom text:**\n{bottom_text}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to save bottom text.")

async def movie_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command - redirect to movie search module"""
    from bot.movie_search import search_movies
    await search_movies(update, context)

async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /download command - redirect to movie search module"""
    from bot.movie_search import download_movie
    await download_movie(update, context)

async def request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /request command for movie requests"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /request <movie name>\n\n"
            "Example: /request The Matrix 1999"
        )
        return
    
    movie_name = " ".join(context.args)
    
    # Create inline keyboard with movie request channel link
    keyboard = [
        [InlineKeyboardButton("🎬 Submit Request", url=MOVIE_SEARCH_CHANNEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎬 **Movie Request Received!**\n\n"
        f"**Movie:** {movie_name}\n\n"
        f"Please submit your request in our movie channel for faster processing!",
        parse_mode='Markdown',
        reply_markup=reply_markup
        )
