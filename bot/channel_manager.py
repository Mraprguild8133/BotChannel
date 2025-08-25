"""
Channel management system
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils import is_admin, get_chat_info
from bot.database import load_json_data, save_json_data

logger = logging.getLogger(__name__)

async def add_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addchannel command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to add channels.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /addchannel <channel_id_or_username>\n\n"
            "Examples:\n"
            "• /addchannel @mychannel\n"
            "• /addchannel -1001234567890\n"
            "• /addchannel https://t.me/mychannel"
        )
        return
    
    channel_input = context.args[0]
    
    # Parse channel input
    if channel_input.startswith('@'):
        channel_username = channel_input[1:]
        channel_id = None
    elif channel_input.startswith('https://t.me/'):
        channel_username = channel_input.split('/')[-1]
        channel_id = None
    else:
        try:
            channel_id = int(channel_input)
            channel_username = None
        except ValueError:
            await update.message.reply_text("❌ Invalid channel format. Use @username, channel ID, or t.me link.")
            return
    
    # Try to get channel info
    try:
        if channel_id:
            chat = await context.bot.get_chat(channel_id)
        else:
            chat = await context.bot.get_chat(f"@{channel_username}")
        
        channel_info = {
            "channel_id": chat.id,
            "channel_name": getattr(chat, 'title', 'Unknown'),
            "channel_username": getattr(chat, 'username', None),
            "added_by": user.id,
            "added_at": datetime.now().isoformat(),
            "is_active": True,
            "member_count": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        # Try to get member count
        try:
            member_count = await context.bot.get_chat_member_count(chat.id)
            channel_info["member_count"] = member_count
        except Exception:
            pass
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed to access channel: {str(e)}\n\n"
            "Make sure:\n"
            "• The bot is added to the channel\n"
            "• The bot has admin rights\n"
            "• The channel ID/username is correct"
        )
        return
    
    # Load current channels
    channels = load_json_data("channels.json")
    
    # Check if channel already exists
    if any(ch['channel_id'] == channel_info['channel_id'] for ch in channels):
        await update.message.reply_text("❌ Channel is already in the list.")
        return
    
    # Add channel
    channels.append(channel_info)
    
    if save_json_data("channels.json", channels):
        await update.message.reply_text(
            f"✅ Successfully added channel!\n\n"
            f"**Channel Details:**\n"
            f"• Name: {channel_info['channel_name']}\n"
            f"• Username: @{channel_info['channel_username'] or 'N/A'}\n"
            f"• ID: `{channel_info['channel_id']}`\n"
            f"• Members: {channel_info['member_count']:,}\n"
            f"• Added by: {user.first_name}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to add channel. Please try again.")

async def remove_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removechannel command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to remove channels.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /removechannel <channel_id_or_username>\n\n"
            "Examples:\n"
            "• /removechannel @mychannel\n"
            "• /removechannel -1001234567890\n"
            "Use /listchannels to see current channels."
        )
        return
    
    channel_input = context.args[0]
    
    # Parse channel input
    if channel_input.startswith('@'):
        channel_identifier = channel_input[1:]
        search_by = 'username'
    else:
        try:
            channel_identifier = int(channel_input)
            search_by = 'id'
        except ValueError:
            await update.message.reply_text("❌ Invalid channel format. Use @username or channel ID.")
            return
    
    # Load current channels
    channels = load_json_data("channels.json")
    
    # Find and remove channel
    channel_found = False
    updated_channels = []
    removed_channel = None
    
    for channel in channels:
        if search_by == 'username' and channel.get('channel_username') == channel_identifier:
            channel_found = True
            channel['is_active'] = False  # Soft delete
            removed_channel = channel
        elif search_by == 'id' and channel['channel_id'] == channel_identifier:
            channel_found = True
            channel['is_active'] = False  # Soft delete
            removed_channel = channel
        updated_channels.append(channel)
    
    if not channel_found:
        await update.message.reply_text("❌ Channel not found in the list.")
        return
    
    if save_json_data("channels.json", updated_channels):
        await update.message.reply_text(
            f"✅ Successfully removed channel!\n\n"
            f"**Removed Channel:**\n"
            f"• Name: {removed_channel['channel_name']}\n"
            f"• Username: @{removed_channel['channel_username'] or 'N/A'}\n"
            f"• ID: `{removed_channel['channel_id']}`\n"
            f"• Removed by: {user.first_name}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to remove channel. Please try again.")

async def list_channels_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listchannels command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to view channels.")
        return
    
    # Load channels
    channels = load_json_data("channels.json")
    active_channels = [ch for ch in channels if ch.get('is_active', True)]
    
    if not active_channels:
        await update.message.reply_text("📺 No channels found.\n\nUse /addchannel to add your first channel.")
        return
    
    # Split into chunks if too many channels
    chunk_size = 10
    channel_chunks = [active_channels[i:i + chunk_size] for i in range(0, len(active_channels), chunk_size)]
    
    for chunk_index, chunk in enumerate(channel_chunks):
        channel_list = f"📺 **Channel List** (Page {chunk_index + 1}/{len(channel_chunks)})\n\n"
        
        for i, channel in enumerate(chunk, chunk_index * chunk_size + 1):
            username = f"@{channel['channel_username']}" if channel.get('channel_username') else "No username"
            member_count = channel.get('member_count', 0)
            
            channel_list += f"**{i}.** {channel['channel_name']}\n"
            channel_list += f"• Username: {username}\n"
            channel_list += f"• ID: `{channel['channel_id']}`\n"
            channel_list += f"• Members: {member_count:,}\n"
            channel_list += f"• Added: {channel.get('added_at', 'Unknown')[:10]}\n\n"
        
        if chunk_index == 0:
            channel_list += f"**Total Active Channels:** {len(active_channels)}"
        
        # Add navigation buttons for multiple pages
        keyboard = []
        if len(channel_chunks) > 1:
            nav_buttons = []
            if chunk_index > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"channels_page_{chunk_index - 1}"))
            if chunk_index < len(channel_chunks) - 1:
                nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"channels_page_{chunk_index + 1}"))
            if nav_buttons:
                keyboard.append(nav_buttons)
        
        # Add management buttons
        keyboard.append([
            InlineKeyboardButton("➕ Add Channel", callback_data="add_channel"),
            InlineKeyboardButton("🗑️ Remove Channel", callback_data="remove_channel")
        ])
        keyboard.append([
            InlineKeyboardButton("📊 Statistics", callback_data="channel_stats"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_channels")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(channel_list, reply_markup=reply_markup, parse_mode='Markdown')

async def channel_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /channelstats command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to view statistics.")
        return
    
    # Load channels
    channels = load_json_data("channels.json")
    active_channels = [ch for ch in channels if ch.get('is_active', True)]
    
    if not active_channels:
        await update.message.reply_text("📊 No channels to analyze.")
        return
    
    # Calculate statistics
    total_channels = len(active_channels)
    total_members = sum(ch.get('member_count', 0) for ch in active_channels)
    avg_members = total_members / total_channels if total_channels > 0 else 0
    
    # Find largest and smallest channels
    channels_with_members = [ch for ch in active_channels if ch.get('member_count', 0) > 0]
    largest_channel = max(channels_with_members, key=lambda x: x.get('member_count', 0)) if channels_with_members else None
    smallest_channel = min(channels_with_members, key=lambda x: x.get('member_count', 0)) if channels_with_members else None
    
    # Recent additions
    recent_channels = sorted(active_channels, key=lambda x: x.get('added_at', ''), reverse=True)[:3]
    
    stats_text = f"""
📊 **Channel Statistics**

**📈 Overview:**
• Total Active Channels: {total_channels}
• Total Members: {total_members:,}
• Average Members: {avg_members:,.0f}
• Inactive Channels: {len(channels) - total_channels}

**🏆 Top Performers:**
"""
    
    if largest_channel:
        stats_text += f"• Largest: {largest_channel['channel_name']} ({largest_channel.get('member_count', 0):,} members)\n"
    
    if smallest_channel and smallest_channel != largest_channel:
        stats_text += f"• Smallest: {smallest_channel['channel_name']} ({smallest_channel.get('member_count', 0):,} members)\n"
    
    stats_text += f"""
**📅 Recent Additions:**
"""
    
    for i, channel in enumerate(recent_channels[:3], 1):
        added_date = channel.get('added_at', 'Unknown')[:10]
        stats_text += f"{i}. {channel['channel_name']} (Added: {added_date})\n"
    
    stats_text += f"""
**📊 Distribution:**
• Large (10K+ members): {len([ch for ch in active_channels if ch.get('member_count', 0) >= 10000])}
• Medium (1K-10K members): {len([ch for ch in active_channels if 1000 <= ch.get('member_count', 0) < 10000])}
• Small (<1K members): {len([ch for ch in active_channels if ch.get('member_count', 0) < 1000])}

**🔄 Management:**
• Channels per Admin: {total_channels / max(1, len(load_json_data("admins.json"))): .1f}
• Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh Stats", callback_data="refresh_stats"),
         InlineKeyboardButton("📺 View Channels", callback_data="view_channels")],
        [InlineKeyboardButton("📈 Export Data", callback_data="export_stats"),
         InlineKeyboardButton("⚙️ Settings", callback_data="channel_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
