#!/usr/bin/env python3
"""
Telegram Bot for Channel Management with Movie Search and Copyright Protection
Main application entry point
"""

import os
import logging
import asyncio
import threading
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from aiohttp import web
from aiohttp.web_runner import GracefulExit
from bot.handlers import (
    start_handler, help_handler, contact_handler, welcome_handler,
    set_welcome_handler, movie_search_handler, download_handler, get_id_handler
)
from bot.admin import (
    admin_panel_handler, add_admin_handler, remove_admin_handler,
    list_admins_handler, admin_stats_handler
)
from bot.channel_manager import (
    add_channel_handler, remove_channel_handler, list_channels_handler,
    channel_stats_handler
)
from bot.copyright_filter import message_filter_handler, add_keyword_handler, remove_keyword_handler, list_keywords_handler, test_ai_detection_handler
from bot.config import BOT_TOKEN
from bot.database import init_database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint for Render.com"""
    return web.Response(text="Bot is running", status=200)

async def webhook_handler(request):
    """Handle webhook updates from Telegram"""
    return web.Response(text="Webhook received", status=200)

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return

    # Get port from environment (for Render.com deployment)
    PORT = int(os.environ.get("PORT", 5000))
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

    logger.info(f"Starting bot in {ENVIRONMENT} mode on port {PORT}")

    # Initialize database
    init_database()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Basic commands
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("contact", contact_handler))
    application.add_handler(CommandHandler("getid", get_id_handler))

    # Welcome message commands
    application.add_handler(CommandHandler("welcome", welcome_handler))
    application.add_handler(CommandHandler("setwelcome", set_welcome_handler))

    # Movie search commands
    application.add_handler(CommandHandler("search", movie_search_handler))
    application.add_handler(CommandHandler("download", download_handler))

    # Admin panel commands
    application.add_handler(CommandHandler("admin", admin_panel_handler))
    application.add_handler(CommandHandler("addadmin", add_admin_handler))
    application.add_handler(CommandHandler("removeadmin", remove_admin_handler))
    application.add_handler(CommandHandler("listadmins", list_admins_handler))
    application.add_handler(CommandHandler("adminstats", admin_stats_handler))

    # Channel management commands
    application.add_handler(CommandHandler("addchannel", add_channel_handler))
    application.add_handler(CommandHandler("removechannel", remove_channel_handler))
    application.add_handler(CommandHandler("listchannels", list_channels_handler))
    application.add_handler(CommandHandler("channelstats", channel_stats_handler))

    # Copyright protection commands
    application.add_handler(CommandHandler("addkeyword", add_keyword_handler))
    application.add_handler(CommandHandler("removekeyword", remove_keyword_handler))
    application.add_handler(CommandHandler("listkeywords", list_keywords_handler))
    application.add_handler(CommandHandler("testai", test_ai_detection_handler))

    # Message filter for copyright protection
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_filter_handler))

    # Callback query handler for inline buttons
    async def callback_query_handler(update, context):
        await update.callback_query.answer()

    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # Add error handler
    async def error_handler(update, context):
        logger.error(f"Exception while handling an update: {context.error}")

    application.add_error_handler(error_handler)

    logger.info("Bot started successfully!")

    # Check if running in production (Render.com) or development
    if ENVIRONMENT == "production":
        # Production mode: Run health check server alongside polling
        async def start_production_server():
            # Create web application for health checks
            web_app = web.Application()
            web_app.router.add_get("/health", health_check)
            web_app.router.add_post("/webhook", webhook_handler)

            # Create and start web server for health checks
            runner = web.AppRunner(web_app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", PORT)
            await site.start()

            logger.info(f"Health check server started on 0.0.0.0:{PORT}")
            logger.info("Bot running in production mode with polling + health server")

            # Keep the health check server alive
            try:
                while True:
                    await asyncio.sleep(10)
            except (KeyboardInterrupt, GracefulExit):
                logger.info("Stopping health check server...")
            finally:
                await runner.cleanup()

        # Start health check server in background
        def run_health_server():
            asyncio.run(start_production_server())

        # Start health check server in separate thread
        health_thread = threading.Thread(target=run_health_server)
        health_thread.daemon = True
        health_thread.start()

        # Start bot with polling in main thread
        logger.info("Starting bot polling in production mode")
        application.run_polling()

    else:
        # Development mode: Use polling + web admin panel
        import web_server
        
        def run_web_server():
            web_server.app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
        
        # Start web server in separate thread
        web_thread = threading.Thread(target=run_web_server)
        web_thread.daemon = True
        web_thread.start()
        
        logger.info(f"Web admin panel started on 0.0.0.0:{PORT}")
        logger.info("Running in development mode with polling")
        application.run_polling()

if __name__ == '__main__':
    main()
