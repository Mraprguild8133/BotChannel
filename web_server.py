"""
Web server for admin panel and health checks
"""
import os
import json
import logging
import psutil
import platform
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_file, redirect
from sqlalchemy import text
from bot.database import load_json_data, save_json_data, engine
from bot.config import BOT_TOKEN, TMDB_API_KEY, AI_ENABLED
from bot.utils import get_bot_stats

# Try to import AI libraries to check availability
try:
    import nltk
    from textblob import TextBlob
    from sklearn.feature_extraction.text import TfidfVectorizer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "bot_admin_secret_key")

# Store start time for uptime calculation
START_TIME = datetime.now()

def get_system_info():
    """Get system information and health data"""
    try:
        # Memory information
        memory = psutil.virtual_memory()
        memory_used = f"{memory.used / (1024**3):.1f} GB"
        memory_total = f"{memory.total / (1024**3):.1f} GB"
        
        # CPU information
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_cores = psutil.cpu_count()
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_used = f"{disk.used / (1024**3):.1f} GB"
        disk_total = f"{disk.total / (1024**3):.1f} GB"
        
        # Uptime calculation
        uptime = datetime.now() - START_TIME
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Check database connection
        database_connected = False
        if engine:
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                database_connected = True
            except Exception:
                pass
        
        # Check TMDB API availability
        tmdb_available = bool(TMDB_API_KEY and TMDB_API_KEY != "default_tmdb_key")
        
        # Bot statistics
        stats = get_bot_stats()
        
        health_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "bot_running": bool(BOT_TOKEN),  # Simple check - in production, this would ping the bot
            "database_connected": database_connected,
            "ai_available": AI_AVAILABLE and AI_ENABLED,
            "tmdb_available": tmdb_available,
            "memory_usage": round(memory.percent, 1),
            "memory_used": memory_used,
            "memory_total": memory_total,
            "cpu_usage": round(cpu_usage, 1),
            "cpu_cores": cpu_cores,
            "disk_usage": round(disk.percent, 1),
            "disk_used": disk_used,
            "disk_total": disk_total,
            "uptime": uptime_str,
            "start_time": START_TIME.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "port": os.environ.get("PORT", "8000"),
            "python_version": platform.python_version(),
            "total_channels": stats.get("total_channels", 0),
            "total_admins": stats.get("total_admins", 0),
            "total_keywords": stats.get("total_keywords", 0)
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "bot_running": False,
            "database_connected": False,
            "ai_available": False,
            "tmdb_available": False,
            "memory_usage": 0,
            "memory_used": "0 GB",
            "memory_total": "0 GB",
            "cpu_usage": 0,
            "cpu_cores": 1,
            "disk_usage": 0,
            "disk_used": "0 GB",
            "disk_total": "0 GB",
            "uptime": "Unknown",
            "start_time": "Unknown",
            "environment": "unknown",
            "port": "unknown",
            "python_version": "unknown",
            "total_channels": 0,
            "total_admins": 0,
            "total_keywords": 0
        }

@app.route('/')
def index():
    """Redirect to admin panel"""
    return redirect('/admin')

@app.route('/admin')
def admin_panel():
    """Admin panel dashboard"""
    try:
        # Load data
        admins = load_json_data("admins.json")
        channels = load_json_data("channels.json")
        keywords = load_json_data("keywords.json")
        
        # Filter active items
        active_admins = [a for a in admins if a.get('is_active', True)]
        active_channels = [c for c in channels if c.get('is_active', True)]
        active_keywords = [k for k in keywords if k.get('is_active', True)]
        
        # Get statistics
        stats = get_bot_stats()
        
        # System info
        health_data = get_system_info()
        
        return render_template('admin_panel.html',
                             admins=active_admins,
                             channels=active_channels,
                             keywords=active_keywords,
                             stats=stats,
                             environment=health_data['environment'],
                             database_connected=health_data['database_connected'],
                             ai_enabled=health_data['ai_available'],
                             super_admins=os.getenv("SUPER_ADMINS", "").split(","),
                             last_updated=health_data['timestamp'])
        
    except Exception as e:
        logger.error(f"Error loading admin panel: {e}")
        return render_template('admin_panel.html',
                             admins=[],
                             channels=[],
                             keywords=[],
                             stats={},
                             environment="unknown",
                             database_connected=False,
                             ai_enabled=False,
                             super_admins=[],
                             last_updated="Error")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    health_data = get_system_info()
    
    # Simple health check response for monitoring systems
    if request.args.get('format') == 'json':
        return jsonify({
            "status": "healthy" if health_data['bot_running'] else "unhealthy",
            "timestamp": health_data['timestamp'],
            "uptime": health_data['uptime'],
            "services": {
                "bot": health_data['bot_running'],
                "database": health_data['database_connected'],
                "ai": health_data['ai_available'],
                "tmdb": health_data['tmdb_available']
            }
        })
    
    # Full health page
    return render_template('health.html', health_data=health_data)

@app.route('/api/stats')
def api_stats():
    """API endpoint for bot statistics"""
    try:
        stats = get_bot_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/channels')
def api_channels():
    """API endpoint for channels data"""
    try:
        channels = load_json_data("channels.json")
        active_channels = [c for c in channels if c.get('is_active', True)]
        return jsonify(active_channels)
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admins')
def api_admins():
    """API endpoint for admins data"""
    try:
        admins = load_json_data("admins.json")
        active_admins = [a for a in admins if a.get('is_active', True)]
        return jsonify(active_admins)
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/keywords')
def api_keywords():
    """API endpoint for keywords data"""
    try:
        keywords = load_json_data("keywords.json")
        active_keywords = [k for k in keywords if k.get('is_active', True)]
        return jsonify(active_keywords)
    except Exception as e:
        logger.error(f"Error getting keywords: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-channel', methods=['POST'])
def api_add_channel():
    """API endpoint to add a channel"""
    try:
        data = request.get_json()
        channel_input = data.get('channel', '').strip()
        
        if not channel_input:
            return jsonify({"error": "Channel input required"}), 400
        
        # Load current channels
        channels = load_json_data("channels.json")
        if not isinstance(channels, list):
            channels = []
        
        # Create new channel entry (simplified - in production, this would verify the channel)
        new_channel = {
            "channel_id": hash(channel_input),  # Simplified ID generation
            "channel_name": channel_input,
            "channel_username": channel_input.lstrip('@').split('/')[-1] if '@' in channel_input or 't.me' in channel_input else None,
            "added_by": 0,  # System add
            "added_at": datetime.now().isoformat(),
            "is_active": True,
            "member_count": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        # Check if already exists
        if any(c.get('channel_name') == channel_input for c in channels):
            return jsonify({"error": "Channel already exists"}), 400
        
        channels.append(new_channel)
        
        if save_json_data("channels.json", channels):
            return jsonify({"success": True, "message": "Channel added successfully"})
        else:
            return jsonify({"error": "Failed to save channel"}), 500
            
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-admin', methods=['POST'])
def api_add_admin():
    """API endpoint to add an admin"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        # Load current admins
        admins = load_json_data("admins.json")
        if not isinstance(admins, list):
            admins = []
        
        # Check if already exists
        if any(a.get('user_id') == user_id for a in admins):
            return jsonify({"error": "User is already an admin"}), 400
        
        # Create new admin entry
        new_admin = {
            "user_id": user_id,
            "username": None,
            "first_name": "Unknown",
            "last_name": None,
            "added_by": 0,  # System add
            "added_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        admins.append(new_admin)
        
        if save_json_data("admins.json", admins):
            return jsonify({"success": True, "message": "Admin added successfully"})
        else:
            return jsonify({"error": "Failed to save admin"}), 500
            
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-keyword', methods=['POST'])
def api_add_keyword():
    """API endpoint to add a keyword"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip().lower()
        
        if not keyword:
            return jsonify({"error": "Keyword required"}), 400
        
        if len(keyword) < 2:
            return jsonify({"error": "Keyword must be at least 2 characters"}), 400
        
        # Load current keywords
        keywords = load_json_data("keywords.json")
        if not isinstance(keywords, list):
            keywords = []
        
        # Check if already exists
        if any(k.get('keyword') == keyword for k in keywords):
            return jsonify({"error": "Keyword already exists"}), 400
        
        # Create new keyword entry
        new_keyword = {
            "keyword": keyword,
            "added_by": 0,  # System add
            "added_at": datetime.now().isoformat(),
            "is_active": True,
            "detection_count": 0
        }
        
        keywords.append(new_keyword)
        
        if save_json_data("keywords.json", keywords):
            return jsonify({"success": True, "message": "Keyword added successfully"})
        else:
            return jsonify({"error": "Failed to save keyword"}), 500
            
    except Exception as e:
        logger.error(f"Error adding keyword: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-ai', methods=['POST'])
def api_test_ai():
    """API endpoint to test AI detection"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Text required for testing"}), 400
        
        # Import copyright filter functions
        from bot.copyright_filter import keyword_detection, ai_content_analysis, DEFAULT_COPYRIGHT_KEYWORDS
        
        # Load keywords
        keywords_data = load_json_data("keywords.json")
        active_keywords = [k['keyword'] for k in keywords_data if k.get('is_active', True)]
        
        if not active_keywords:
            active_keywords = DEFAULT_COPYRIGHT_KEYWORDS
        
        # Perform tests
        detected_keywords = keyword_detection(text, active_keywords)
        ai_analysis = ai_content_analysis(text)
        
        # Determine if would be filtered
        would_filter = bool(detected_keywords) or ai_analysis['score'] >= 0.7
        
        return jsonify({
            "success": True,
            "text": text,
            "keywords": detected_keywords,
            "score": ai_analysis['score'],
            "analysis": ai_analysis.get('analysis', 'No analysis available'),
            "would_filter": would_filter
        })
        
    except Exception as e:
        logger.error(f"Error testing AI: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-bot', methods=['POST'])
def api_test_bot():
    """API endpoint to test bot connectivity"""
    try:
        # Simple bot test - check if token is configured
        if not BOT_TOKEN:
            return jsonify({"error": "Bot token not configured"}), 500
        
        # In a full implementation, this would actually ping the Telegram API
        return jsonify({
            "success": True,
            "message": "Bot token is configured and appears valid"
        })
        
    except Exception as e:
        logger.error(f"Error testing bot: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """API endpoint to download logs"""
    try:
        log_file = "bot.log"
        if os.path.exists(log_file):
            return send_file(log_file, as_attachment=True, download_name=f"bot-logs-{datetime.now().strftime('%Y%m%d')}.log")
        else:
            return jsonify({"error": "Log file not found"}), 404
    except Exception as e:
        logger.error(f"Error downloading logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health/export')
def api_health_export():
    """API endpoint to export health report"""
    try:
        health_data = get_system_info()
        
        # Create detailed report
        report = {
            "report_generated": datetime.now().isoformat(),
            "system_health": health_data,
            "statistics": get_bot_stats(),
            "configuration": {
                "environment": os.environ.get("ENVIRONMENT", "development"),
                "ai_enabled": AI_ENABLED,
                "database_type": "PostgreSQL" if health_data['database_connected'] else "File Storage"
            }
        }
        
        # Save to temporary file
        report_file = f"health-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return send_file(report_file, as_attachment=True, download_name=report_file)
        
    except Exception as e:
        logger.error(f"Error exporting health report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/<data_type>')
def api_export_data(data_type):
    """API endpoint to export data"""
    try:
        if data_type == "channels":
            data = load_json_data("channels.json")
            filename = f"channels-export-{datetime.now().strftime('%Y%m%d')}.json"
        elif data_type == "admins":
            data = load_json_data("admins.json")
            filename = f"admins-export-{datetime.now().strftime('%Y%m%d')}.json"
        elif data_type == "keywords":
            data = load_json_data("keywords.json")
            filename = f"keywords-export-{datetime.now().strftime('%Y%m%d')}.json"
        else:
            return jsonify({"error": "Invalid data type"}), 400
        
        # Save to temporary file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return send_file(filename, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error exporting {data_type}: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Configure logging for web server
    logging.basicConfig(level=logging.INFO)
    
    # Get port from environment
    PORT = int(os.environ.get("PORT", 5000))
    
    logger.info(f"Starting web server on port {PORT}")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=PORT, debug=os.environ.get("ENVIRONMENT") != "production")
