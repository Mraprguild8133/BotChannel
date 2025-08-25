"""
Basic bot command handlers
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils import is_admin, get_user_info
from bot.database import load_json_data, save_json_data

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat = update.effective_chat
    
    logger.info(f"Start command from user {user.id} in chat {chat.id}")
    
    welcome_text = f"""
🤖 **Welcome to Channel Management Bot!**

Hello {user.first_name}! I'm here to help you manage your Telegram channels with advanced features.

**🔧 Main Features:**
• Channel Management
• Movie Search & Download
• AI-Powered Copyright Protection
• Multi-Admin System
• Custom Welcome Messages

**📋 Available Commands:**
/help - Show all commands
/admin - Admin panel (admin only)
/search <movie> - Search for movies
/welcome - Show welcome message
/contact - Contact information

**🛡️ Security Features:**
• Automatic content filtering
• Copyright protection
• Keyword detection
• AI-powered moderation

Use /help to see all available commands!
    """
    
    keyboard = [
        [InlineKeyboardButton("📋 Help", callback_data="/help"),
         InlineKeyboardButton("🔧 Admin Panel", callback_data="/admin")],
        [InlineKeyboardButton("🎬 Search Movies", callback_data="/search"),
         InlineKeyboardButton("📞 Contact", callback_data="/contact")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    logger.info(f"Help command from user {user.id}")
    
    help_text = """
📋 **Bot Commands Help**

**🔧 Basic Commands:**
/start - Start the bot
/help - Show this help message
/contact - Show contact information
/getid - Get your user/chat ID

**👋 Welcome Messages:**
/welcome - Show current welcome message
/setwelcome <message> - Set welcome message (admin only)

**🎬 Movie Search:**
/search <movie name> - Search for movies
/download <movie id> - Get download link

**👑 Admin Commands:**
/admin - Show admin panel
/addadmin <user_id> - Add new admin
/removeadmin <user_id> - Remove admin
/listadmins - List all admins
/adminstats - Show admin statistics

**📺 Channel Management:**
/addchannel <channel_id> - Add channel
/removechannel <channel_id> - Remove channel
/listchannels - List all channels
/channelstats - Show channel statistics

**🛡️ Copyright Protection:**
/addkeyword <keyword> - Add filter keyword
/removekeyword <keyword> - Remove keyword
/listkeywords - List all keywords
/testai <text> - Test AI detection

**💡 Tips:**
• Use channel username or ID for channel commands
• Keywords are case-insensitive
• AI detection works on text analysis
• Only admins can modify settings
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /contact command"""
    contact_text = """
📞 **Contact Information**

**Bot Developer:** Mraprguild 
**Support Group:** @mraprguildsupport
**Group Management:** @aprgrouphelpbot

**🆘 Need Help?**
• Join our support group for quick assistance
• Check the documentation on our Group Management 
• Report bugs or suggest features

**📧 Direct Contact:**
• Email: mraprguild@gmail.com
• Telegram: @Sathishkumar33

**🕐 Support Hours:**
Monday - Friday: 9:00 AM - 6:00 PM UTC
Weekend: Limited support available

Thank you for using our bot! 🤖
    """
    
    keyboard = [
        [InlineKeyboardButton("💬 Support Group", url="https://t.me/mraprguildsupport"),
         InlineKeyboardButton("📢 Updates Channel", url="https://t.me/+Z3ImQkd3of1iNmY9")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(contact_text, reply_markup=reply_markup, parse_mode='Markdown')

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
    """Handle /welcome command"""
    chat_id = update.effective_chat.id
    
    # Load welcome messages
    welcome_messages = load_json_data("welcome_messages.json")
    
    if str(chat_id) in welcome_messages:
        welcome_text = welcome_messages[str(chat_id)]["message"]
    else:
        welcome_text = """
👋 **Default Welcome Message**

Welcome to our group! Please read the rules and enjoy your stay.

**Group Rules:**
• Be respectful to all members
• No spam or advertising
• Stay on topic
• Follow Telegram ToS

Have a great time! 🎉
        """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

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
    welcome_messages[str(chat.id)] = {
        "message": welcome_message,
        "set_by": user.id,
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

async def movie_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command - redirect to movie search module"""
    from bot.movie_search import search_movies
    await search_movies(update, context)

async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /download command - redirect to movie search module"""
    from bot.movie_search import download_movie
    await download_movie(update, context)
