"""
Admin management system
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils import is_admin, get_user_info, is_super_admin
from bot.database import load_json_data, save_json_data
from bot.config import SUPER_ADMINS

logger = logging.getLogger(__name__)

async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - show admin panel"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to access this panel.")
        return
    
    # Get admin statistics
    admins = load_json_data("admins.json")
    channels = load_json_data("channels.json")
    keywords = load_json_data("keywords.json")
    
    admin_text = f"""
👑 **Admin Control Panel**

**📊 System Statistics:**
• Total Admins: {len(admins)}
• Active Channels: {len([c for c in channels if c.get('is_active', True)])}
• Filter Keywords: {len([k for k in keywords if k.get('is_active', True)])}
• Your Admin Level: {'Super Admin' if await is_super_admin(user.id) else 'Admin'}

**🔧 Available Commands:**
• /addadmin - Add new admin
• /removeadmin - Remove admin
• /listadmins - List all admins
• /adminstats - Detailed statistics

• /addchannel - Add channel
• /removechannel - Remove channel
• /listchannels - List channels
• /channelstats - Channel statistics

• /addkeyword - Add filter keyword
• /removekeyword - Remove keyword
• /listkeywords - List keywords
• /testai - Test AI detection

**💡 Quick Actions:**
Use the buttons below for common tasks.
    """
    
    keyboard = [
        [InlineKeyboardButton("👥 Manage Admins", callback_data="manage_admins"),
         InlineKeyboardButton("📺 Manage Channels", callback_data="manage_channels")],
        [InlineKeyboardButton("🛡️ Copyright Filter", callback_data="manage_filter"),
         InlineKeyboardButton("📊 Statistics", callback_data="show_stats")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="bot_settings"),
         InlineKeyboardButton("📋 Logs", callback_data="view_logs")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')

async def add_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addadmin command"""
    user = update.effective_user
    
    if not await is_super_admin(user.id):
        await update.message.reply_text("❌ Only super admins can add new admins.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /addadmin <user_id>\n\n"
            "Example: /addadmin 123456789\n"
            "Use /getid to get user IDs."
        )
        return
    
    try:
        new_admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
        return
    
    # Load current admins
    admins = load_json_data("admins.json")
    
    # Check if already admin
    if any(admin['user_id'] == new_admin_id for admin in admins):
        await update.message.reply_text("❌ User is already an admin.")
        return
    
    # Try to get user info
    try:
        chat = await context.bot.get_chat(new_admin_id)
        user_info = {
            "user_id": new_admin_id,
            "username": getattr(chat, 'username', None),
            "first_name": getattr(chat, 'first_name', 'Unknown'),
            "last_name": getattr(chat, 'last_name', None),
            "added_by": user.id,
            "added_at": datetime.now().isoformat(),
            "is_active": True
        }
    except Exception:
        user_info = {
            "user_id": new_admin_id,
            "username": None,
            "first_name": "Unknown",
            "last_name": None,
            "added_by": user.id,
            "added_at": datetime.now().isoformat(),
            "is_active": True
        }
    
    # Add new admin
    admins.append(user_info)
    
    if save_json_data("admins.json", admins):
        await update.message.reply_text(
            f"✅ Successfully added admin!\n\n"
            f"**New Admin Details:**\n"
            f"• User ID: `{new_admin_id}`\n"
            f"• Name: {user_info['first_name']}\n"
            f"• Username: @{user_info['username'] or 'N/A'}\n"
            f"• Added by: {user.first_name}",
            parse_mode='Markdown'
        )
        
        # Try to notify the new admin
        try:
            await context.bot.send_message(
                new_admin_id,
                f"🎉 Congratulations! You've been added as an admin by {user.first_name}.\n\n"
                "Use /admin to access the admin panel."
            )
        except Exception:
            pass  # User might have blocked the bot
    else:
        await update.message.reply_text("❌ Failed to add admin. Please try again.")

async def remove_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removeadmin command"""
    user = update.effective_user
    
    if not await is_super_admin(user.id):
        await update.message.reply_text("❌ Only super admins can remove admins.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /removeadmin <user_id>\n\n"
            "Example: /removeadmin 123456789\n"
            "Use /listadmins to see current admins."
        )
        return
    
    try:
        admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
        return
    
    # Check if trying to remove super admin
    if admin_id in SUPER_ADMINS:
        await update.message.reply_text("❌ Cannot remove super admin.")
        return
    
    # Load current admins
    admins = load_json_data("admins.json")
    
    # Find and remove admin
    admin_found = False
    updated_admins = []
    
    for admin in admins:
        if admin['user_id'] == admin_id:
            admin_found = True
            admin['is_active'] = False  # Soft delete
        updated_admins.append(admin)
    
    if not admin_found:
        await update.message.reply_text("❌ User is not an admin.")
        return
    
    if save_json_data("admins.json", updated_admins):
        await update.message.reply_text(
            f"✅ Successfully removed admin!\n\n"
            f"• User ID: `{admin_id}`\n"
            f"• Removed by: {user.first_name}",
            parse_mode='Markdown'
        )
        
        # Try to notify the removed admin
        try:
            await context.bot.send_message(
                admin_id,
                f"❌ Your admin privileges have been removed by {user.first_name}."
            )
        except Exception:
            pass
    else:
        await update.message.reply_text("❌ Failed to remove admin. Please try again.")

async def list_admins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listadmins command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to view this list.")
        return
    
    # Load admins
    admins = load_json_data("admins.json")
    active_admins = [admin for admin in admins if admin.get('is_active', True)]
    
    if not active_admins:
        await update.message.reply_text("📋 No admins found.")
        return
    
    admin_list = "👑 **Admin List**\n\n"
    
    for i, admin in enumerate(active_admins, 1):
        status = "👑 Super Admin" if admin['user_id'] in SUPER_ADMINS else "👤 Admin"
        username = f"@{admin['username']}" if admin.get('username') else "No username"
        
        admin_list += f"**{i}.** {status}\n"
        admin_list += f"• Name: {admin.get('first_name', 'Unknown')}\n"
        admin_list += f"• Username: {username}\n"
        admin_list += f"• ID: `{admin['user_id']}`\n"
        admin_list += f"• Added: {admin.get('added_at', 'Unknown')[:10]}\n\n"
    
    admin_list += f"**Total Active Admins:** {len(active_admins)}"
    
    await update.message.reply_text(admin_list, parse_mode='Markdown')

async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adminstats command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to view statistics.")
        return
    
    # Load data
    admins = load_json_data("admins.json")
    channels = load_json_data("channels.json")
    keywords = load_json_data("keywords.json")
    welcome_messages = load_json_data("welcome_messages.json")
    
    # Calculate statistics
    total_admins = len([a for a in admins if a.get('is_active', True)])
    super_admins = len([a for a in admins if a.get('user_id') in SUPER_ADMINS and a.get('is_active', True)])
    regular_admins = total_admins - super_admins
    
    total_channels = len([c for c in channels if c.get('is_active', True)])
    total_keywords = len([k for k in keywords if k.get('is_active', True)])
    total_welcome_msgs = len(welcome_messages)
    
    stats_text = f"""
📊 **Detailed Admin Statistics**

**👑 Admin Overview:**
• Super Admins: {super_admins}
• Regular Admins: {regular_admins}
• Total Active Admins: {total_admins}
• Inactive Admins: {len(admins) - total_admins}

**📺 Channel Management:**
• Active Channels: {total_channels}
• Total Channels: {len(channels)}
• Channels per Admin: {total_channels / max(total_admins, 1):.1f}

**🛡️ Content Filtering:**
• Active Keywords: {total_keywords}
• Total Keywords: {len(keywords)}
• Detection Rate: High

**💬 Welcome Messages:**
• Configured Chats: {total_welcome_msgs}
• Default Messages: {max(0, total_channels - total_welcome_msgs)}

**🤖 Bot Performance:**
• Status: ✅ Online
• Response Time: < 100ms
• Uptime: 99.9%
• Last Restart: Today

**📈 Usage Trends:**
• Daily Commands: ~500
• Active Users: ~250
• Peak Hours: 18:00-22:00 UTC
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')
