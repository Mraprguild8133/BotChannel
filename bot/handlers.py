"""
Basic command handlers for the Telegram bot
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .config import CONTACT_INFO, MOVIE_SEARCH_CHANNEL, MOVIE_DOWNLOAD_CHANNEL, GITHUB_URL, SHORTENER_URL
from .database import get_welcome_message, set_welcome_message
from .url_shortener import shorten_url
from .movie_search import search_movie, get_download_link

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    if not update.message or not update.effective_user:
        return
    
    user = update.effective_user
    welcome_msg = get_welcome_message()
    
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
            InlineKeyboardButton("📞 Contact", callback_data="contact")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""
🎬 **Welcome to Mrapr Guild Movie Bot!**

Hello {user.first_name}! 👋

{welcome_msg['message']}

**Available Commands:**
🔍 /search [movie name] - Search for movies
📥 /download [movie name] - Get download links
💬 /contact - Contact information
❓ /help - Show all commands

{welcome_msg['bottom_text']}

**Our Channels:**
🎬 Movie Requests: {MOVIE_SEARCH_CHANNEL}
📥 Movie Downloads: {MOVIE_DOWNLOAD_CHANNEL}
🌐 Website: {SHORTENER_URL}
💻 GitHub: {GITHUB_URL}
"""
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    if not update.message:
        return
    help_text = """
🤖 **Mrapr Guild Movie Bot - Help**

**User Commands:**
🔍 `/search [movie name]` - Search for movies
📥 `/download [movie name]` - Get download links
💬 `/contact` - Contact information
🏠 `/start` - Show welcome message
❓ `/help` - Show this help

**Admin Commands:**
👑 `/admin` - Admin panel
👤 `/addadmin [user_id]` - Add admin
❌ `/removeadmin [user_id]` - Remove admin
📋 `/listadmins` - List all admins
📊 `/adminstats` - Admin statistics
📺 `/addchannel [channel_id]` - Add channel
🗑️ `/removechannel [channel_id]` - Remove channel
📋 `/listchannels` - List channels
📊 `/channelstats` - Channel statistics
🚫 `/addkeyword [keyword]` - Add copyright keyword
✅ `/removekeyword [keyword]` - Remove keyword
🧠 `/testai [text]` - Test AI copyright detection
💬 `/setwelcome [message]` - Set welcome message

**Our Services:**
🎬 Movie Search: {MOVIE_SEARCH_CHANNEL}
📥 Movie Downloads: {MOVIE_DOWNLOAD_CHANNEL}
🌐 URL Shortener: {SHORTENER_URL}
💻 GitHub Project: {GITHUB_URL}
📞 Contact: {CONTACT_TELEGRAM}
""".format(
        MOVIE_SEARCH_CHANNEL=MOVIE_SEARCH_CHANNEL,
        MOVIE_DOWNLOAD_CHANNEL=MOVIE_DOWNLOAD_CHANNEL,
        SHORTENER_URL=SHORTENER_URL,
        GITHUB_URL=GITHUB_URL,
        CONTACT_TELEGRAM=CONTACT_INFO['telegram']
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown', disable_web_page_preview=True)

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /contact command"""
    if not update.message:
        return
    contact_text = f"""
📞 **Contact Information**

👨‍💻 **Developer:** Sathish Kumar
📱 **Telegram:** {CONTACT_INFO['telegram']}
🌐 **Website:** {SHORTENER_URL}
💻 **GitHub:** {GITHUB_URL}

**Our Channels:**
🎬 **Movie Requests:** {MOVIE_SEARCH_CHANNEL}
📥 **Movie Downloads:** {MOVIE_DOWNLOAD_CHANNEL}

**For Support:**
• Technical Issues: Contact via Telegram
• Movie Requests: Use our movie request channel
• Bug Reports: Create an issue on GitHub

**Business Inquiries:**
Contact us through Telegram for partnerships and collaborations.
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📱 Contact on Telegram", url=f"https://t.me/{CONTACT_INFO['telegram'].replace('@', '')}")
        ],
        [
            InlineKeyboardButton("🎬 Movie Requests", url=MOVIE_SEARCH_CHANNEL),
            InlineKeyboardButton("📥 Downloads", url=MOVIE_DOWNLOAD_CHANNEL)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        contact_text,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /welcome command - show current welcome message"""
    if not update.message:
        return
    welcome_msg = get_welcome_message()
    
    message = f"""
📋 **Current Welcome Configuration**

**Welcome Message:**
{welcome_msg['message']}

**Bottom Text:**
{welcome_msg['bottom_text']}

**Last Updated:** {welcome_msg.get('last_updated', 'Not set')}

Use `/setwelcome [message]` to update the welcome message.
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def set_welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setwelcome command - set welcome message"""
    if not update.message or not update.effective_user:
        return
        
    from .admin import is_admin
    
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: `/setwelcome [message]`", parse_mode='Markdown')
        return
    
    new_message = ' '.join(context.args)
    current_config = get_welcome_message()
    
    success = set_welcome_message(new_message, current_config['bottom_text'])
    
    if success:
        await update.message.reply_text("✅ Welcome message updated successfully!")
        logger.info(f"Welcome message updated by admin {update.effective_user.id}")
    else:
        await update.message.reply_text("❌ Failed to update welcome message.")

async def movie_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command - search for movies"""
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: `/search [movie name]`\n\n"
            f"Or visit our movie request channel: {MOVIE_SEARCH_CHANNEL}",
            parse_mode='Markdown'
        )
        return
    
    movie_name = ' '.join(context.args)
    await update.message.reply_text("🔍 Searching for movies...")
    
    try:
        results = await search_movie(movie_name)
        
        if not results:
            message = f"""
❌ **No results found for:** {movie_name}

**Try:**
• Check spelling
• Use different keywords
• Visit our movie request channel: {MOVIE_SEARCH_CHANNEL}
"""
        else:
            message = f"🎬 **Search Results for:** {movie_name}\n\n"
            for i, movie in enumerate(results[:5], 1):
                message += f"{i}. **{movie['title']}**\n"
                if movie.get('year'):
                    message += f"   📅 Year: {movie['year']}\n"
                if movie.get('quality'):
                    message += f"   📺 Quality: {movie['quality']}\n"
                message += "\n"
            
            message += f"\n📥 Use `/download [movie name]` to get download links"
            message += f"\n🎬 More movies: {MOVIE_DOWNLOAD_CHANNEL}"
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 Request Channel", url=MOVIE_SEARCH_CHANNEL),
                InlineKeyboardButton("📥 Download Channel", url=MOVIE_DOWNLOAD_CHANNEL)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error in movie search: {e}")
        await update.message.reply_text(
            "❌ An error occurred while searching. Please try again later or "
            f"visit our request channel: {MOVIE_SEARCH_CHANNEL}"
        )

async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /download command - get download links"""
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: `/download [movie name]`\n\n"
            f"Or visit our download channel: {MOVIE_DOWNLOAD_CHANNEL}",
            parse_mode='Markdown'
        )
        return
    
    movie_name = ' '.join(context.args)
    await update.message.reply_text("📥 Getting download links...")
    
    try:
        download_link = await get_download_link(movie_name)
        
        if not download_link:
            message = f"""
❌ **Download not available for:** {movie_name}

**Options:**
• Request in our channel: {MOVIE_SEARCH_CHANNEL}
• Check our download channel: {MOVIE_DOWNLOAD_CHANNEL}
• Try searching with different keywords
"""
        else:
            # Shorten the download link
            shortened_link = await shorten_url(download_link)
            
            message = f"""
📥 **Download Available:** {movie_name}

🔗 **Download Link:** {shortened_link}

⚠️ **Note:** 
• Links are provided for educational purposes
• Respect copyright laws in your country
• Support original creators when possible

📺 More downloads: {MOVIE_DOWNLOAD_CHANNEL}
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 Request More", url=MOVIE_SEARCH_CHANNEL),
                InlineKeyboardButton("📥 Download Channel", url=MOVIE_DOWNLOAD_CHANNEL)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error in download handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred while getting download links. "
            f"Please visit our download channel: {MOVIE_DOWNLOAD_CHANNEL}"
        )

async def get_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getid command - get user's Telegram ID"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    message = f"""
🆔 **Your Telegram Information**

**User ID:** `{user_id}`
**Username:** @{username if username else 'Not set'}
**Name:** {first_name}

**To become an admin:**
Send this User ID to the bot owner: `{user_id}`
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')
