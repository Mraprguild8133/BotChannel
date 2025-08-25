"""
AI-powered copyright protection and content filtering
"""
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import is_admin
from bot.database import load_json_data, save_json_data
from bot.config import AI_ENABLED, COPYRIGHT_THRESHOLD

# Try to import AI libraries
try:
    import nltk
    from textblob import TextBlob
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Download required NLTK data
if AI_AVAILABLE:
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
    except Exception:
        pass

# Copyright-related keywords
DEFAULT_COPYRIGHT_KEYWORDS = [
    'pirated', 'illegal download', 'torrent', 'cracked', 'leaked',
    'copyright infringement', 'dmca', 'unauthorized', 'bootleg',
    'cam rip', 'screener', 'dvdrip', 'brrip', 'webrip',
    'movie leak', 'free movie', 'download movie', 'watch free'
]

def preprocess_text(text):
    """Preprocess text for AI analysis"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove special characters but keep spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def keyword_detection(text, keywords):
    """Basic keyword-based detection"""
    text_lower = text.lower()
    detected_keywords = []
    
    for keyword in keywords:
        if keyword.lower() in text_lower:
            detected_keywords.append(keyword)
    
    return detected_keywords

def ai_content_analysis(text):
    """AI-powered content analysis"""
    if not AI_AVAILABLE or not AI_ENABLED:
        return {"score": 0.0, "analysis": "AI analysis not available"}
    
    try:
        # Preprocess text
        processed_text = preprocess_text(text)
        
        if not processed_text:
            return {"score": 0.0, "analysis": "No meaningful content"}
        
        # Analyze sentiment and content
        blob = TextBlob(processed_text)
        sentiment = blob.sentiment
        
        # Check for copyright-related patterns
        copyright_patterns = [
            r'download.*movie',
            r'watch.*free',
            r'(pirat|crack|leak).*',
            r'(torrent|magnet|direct).*link',
            r'(hd|full).*movie.*free'
        ]
        
        pattern_matches = 0
        for pattern in copyright_patterns:
            if re.search(pattern, processed_text):
                pattern_matches += 1
        
        # Calculate copyright risk score
        risk_score = 0.0
        
        # Pattern-based scoring
        risk_score += (pattern_matches / len(copyright_patterns)) * 0.4
        
        # Sentiment-based scoring (negative sentiment might indicate piracy)
        if sentiment.polarity < -0.3:
            risk_score += 0.2
        
        # Length-based scoring (longer messages with keywords are riskier)
        if len(processed_text.split()) > 20 and pattern_matches > 0:
            risk_score += 0.2
        
        # Keyword density
        total_words = len(processed_text.split())
        if total_words > 0:
            keyword_density = pattern_matches / total_words
            risk_score += min(keyword_density * 2, 0.3)
        
        # Normalize score
        risk_score = min(risk_score, 1.0)
        
        analysis = {
            "score": risk_score,
            "sentiment": sentiment.polarity,
            "pattern_matches": pattern_matches,
            "analysis": f"Risk: {risk_score:.2f}, Sentiment: {sentiment.polarity:.2f}"
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return {"score": 0.0, "analysis": f"Analysis error: {str(e)}"}

async def message_filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages for copyright filtering"""
    message = update.message
    if not message or not message.text:
        return
    
    user = message.from_user
    chat = message.chat
    text = message.text
    
    # Skip messages from admins
    if await is_admin(user.id):
        return
    
    # Load filter keywords
    keywords_data = load_json_data("keywords.json")
    active_keywords = [k['keyword'] for k in keywords_data if k.get('is_active', True)]
    
    # Add default keywords if none exist
    if not active_keywords:
        active_keywords = DEFAULT_COPYRIGHT_KEYWORDS
    
    # Perform keyword detection
    detected_keywords = keyword_detection(text, active_keywords)
    
    # Perform AI analysis
    ai_analysis = ai_content_analysis(text)
    
    # Determine if message should be filtered
    should_filter = False
    filter_reason = []
    
    if detected_keywords:
        should_filter = True
        filter_reason.append(f"Keywords: {', '.join(detected_keywords[:3])}")
    
    if ai_analysis['score'] >= COPYRIGHT_THRESHOLD:
        should_filter = True
        filter_reason.append(f"AI Risk: {ai_analysis['score']:.2f}")
    
    # Log the analysis
    logger.info(f"Message analysis - User: {user.id}, Chat: {chat.id}, "
               f"Keywords: {len(detected_keywords)}, AI Score: {ai_analysis['score']:.2f}, "
               f"Filtered: {should_filter}")
    
    # Take action if message should be filtered
    if should_filter:
        try:
            # Delete the message
            await message.delete()
            
            # Send warning to user
            warning_message = f"""
🚫 **Message Filtered**

{user.first_name}, your message was automatically removed for potential copyright violation.

**Reason:** {' | '.join(filter_reason)}

Please ensure your messages comply with copyright laws and community guidelines.
            """
            
            warning = await context.bot.send_message(
                chat.id,
                warning_message,
                parse_mode='Markdown'
            )
            
            # Delete warning after 30 seconds
            context.job_queue.run_once(
                lambda context: context.bot.delete_message(chat.id, warning.message_id),
                30
            )
            
            # Update keyword detection count
            for keyword_data in keywords_data:
                if keyword_data['keyword'] in detected_keywords:
                    keyword_data['detection_count'] = keyword_data.get('detection_count', 0) + 1
            
            save_json_data("keywords.json", keywords_data)
            
            # Notify admins in private (optional)
            admin_notification = f"""
🚨 **Copyright Filter Alert**

**Filtered Message:**
• User: {user.first_name} (@{user.username or 'N/A'})
• Chat: {chat.title or 'Private'}
• Keywords: {', '.join(detected_keywords) if detected_keywords else 'None'}
• AI Score: {ai_analysis['score']:.2f}
• Message: {text[:100]}...
            """
            
            # Send to admins (implement admin notification logic here)
            
        except Exception as e:
            logger.error(f"Failed to filter message: {e}")

async def add_keyword_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addkeyword command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to add keywords.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /addkeyword <keyword>\n\n"
            "Example: /addkeyword pirated movie\n"
            "Keywords are case-insensitive."
        )
        return
    
    keyword = " ".join(context.args).lower().strip()
    
    if len(keyword) < 2:
        await update.message.reply_text("❌ Keyword must be at least 2 characters long.")
        return
    
    # Load current keywords
    keywords = load_json_data("keywords.json")
    
    # Check if keyword already exists
    if any(k['keyword'].lower() == keyword for k in keywords):
        await update.message.reply_text("❌ Keyword already exists.")
        return
    
    # Add new keyword
    new_keyword = {
        "keyword": keyword,
        "added_by": user.id,
        "added_at": datetime.now().isoformat(),
        "is_active": True,
        "detection_count": 0
    }
    
    keywords.append(new_keyword)
    
    if save_json_data("keywords.json", keywords):
        await update.message.reply_text(
            f"✅ Successfully added keyword!\n\n"
            f"**Keyword:** `{keyword}`\n"
            f"**Added by:** {user.first_name}\n"
            f"**Total keywords:** {len([k for k in keywords if k.get('is_active', True)])}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to add keyword. Please try again.")

async def remove_keyword_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removekeyword command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to remove keywords.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /removekeyword <keyword>\n\n"
            "Example: /removekeyword pirated movie\n"
            "Use /listkeywords to see current keywords."
        )
        return
    
    keyword = " ".join(context.args).lower().strip()
    
    # Load current keywords
    keywords = load_json_data("keywords.json")
    
    # Find and remove keyword
    keyword_found = False
    updated_keywords = []
    
    for kw in keywords:
        if kw['keyword'].lower() == keyword:
            keyword_found = True
            kw['is_active'] = False  # Soft delete
        updated_keywords.append(kw)
    
    if not keyword_found:
        await update.message.reply_text("❌ Keyword not found.")
        return
    
    if save_json_data("keywords.json", updated_keywords):
        await update.message.reply_text(
            f"✅ Successfully removed keyword!\n\n"
            f"**Keyword:** `{keyword}`\n"
            f"**Removed by:** {user.first_name}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to remove keyword. Please try again.")

async def list_keywords_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listkeywords command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to view keywords.")
        return
    
    # Load keywords
    keywords = load_json_data("keywords.json")
    active_keywords = [k for k in keywords if k.get('is_active', True)]
    
    if not active_keywords:
        await update.message.reply_text(
            "📋 No keywords configured.\n\n"
            "Default copyright keywords are being used.\n"
            "Use /addkeyword to add custom keywords."
        )
        return
    
    keyword_list = "🛡️ **Filter Keywords**\n\n"
    
    for i, keyword in enumerate(active_keywords, 1):
        detection_count = keyword.get('detection_count', 0)
        added_date = keyword.get('added_at', 'Unknown')[:10]
        
        keyword_list += f"**{i}.** `{keyword['keyword']}`\n"
        keyword_list += f"• Detections: {detection_count}\n"
        keyword_list += f"• Added: {added_date}\n\n"
    
    keyword_list += f"**Total Active Keywords:** {len(active_keywords)}\n"
    keyword_list += f"**AI Analysis:** {'✅ Enabled' if AI_ENABLED and AI_AVAILABLE else '❌ Disabled'}\n"
    keyword_list += f"**Detection Threshold:** {COPYRIGHT_THRESHOLD}"
    
    await update.message.reply_text(keyword_list, parse_mode='Markdown')

async def test_ai_detection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /testai command"""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You need admin privileges to test AI detection.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /testai <text to analyze>\n\n"
            "Example: /testai Download the latest movie for free here\n"
            "This will test the AI copyright detection on the provided text."
        )
        return
    
    test_text = " ".join(context.args)
    
    # Load keywords for testing
    keywords_data = load_json_data("keywords.json")
    active_keywords = [k['keyword'] for k in keywords_data if k.get('is_active', True)]
    
    if not active_keywords:
        active_keywords = DEFAULT_COPYRIGHT_KEYWORDS
    
    # Perform keyword detection
    detected_keywords = keyword_detection(test_text, active_keywords)
    
    # Perform AI analysis
    ai_analysis = ai_content_analysis(test_text)
    
    # Generate test results
    test_results = f"""
🧪 **AI Detection Test Results**

**Input Text:**
`{test_text[:200]}{'...' if len(test_text) > 200 else ''}`

**Keyword Detection:**
• Found: {len(detected_keywords)} keywords
• Keywords: {', '.join(detected_keywords[:5]) if detected_keywords else 'None'}

**AI Analysis:**
• Risk Score: {ai_analysis['score']:.3f} / 1.000
• Threshold: {COPYRIGHT_THRESHOLD}
• Status: {'🚫 WOULD BE FILTERED' if ai_analysis['score'] >= COPYRIGHT_THRESHOLD else '✅ WOULD PASS'}
• Details: {ai_analysis.get('analysis', 'N/A')}

**Overall Result:**
"""
    
    would_filter = detected_keywords or ai_analysis['score'] >= COPYRIGHT_THRESHOLD
    
    if would_filter:
        filter_reasons = []
        if detected_keywords:
            filter_reasons.append(f"Keywords ({len(detected_keywords)})")
        if ai_analysis['score'] >= COPYRIGHT_THRESHOLD:
            filter_reasons.append(f"AI Risk ({ai_analysis['score']:.2f})")
        
        test_results += f"🚫 **FILTERED** - Reason: {' + '.join(filter_reasons)}"
    else:
        test_results += "✅ **PASSED** - No copyright violations detected"
    
    test_results += f"\n\n**System Status:**\n"
    test_results += f"• AI Available: {'✅' if AI_AVAILABLE else '❌'}\n"
    test_results += f"• AI Enabled: {'✅' if AI_ENABLED else '❌'}\n"
    test_results += f"• Active Keywords: {len(active_keywords)}"
    
    await update.message.reply_text(test_results, parse_mode='Markdown')
