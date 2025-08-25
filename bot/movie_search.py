"""
Movie search and download functionality using TMDB API
"""
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import TMDB_API_KEY

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

async def search_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for movies using TMDB API"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /search <movie name>\n\n"
            "Example: /search Avengers Endgame\n"
            "This will search for movies matching your query."
        )
        return
    
    query = " ".join(context.args)
    
    try:
        # Search for movies using TMDB API
        search_url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "en-US",
            "page": 1,
            "include_adult": False
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code == 401:
            await update.message.reply_text(
                "❌ Movie search service is currently unavailable.\n"
                "Please contact administrators."
            )
            return
        
        response.raise_for_status()
        data = response.json()
        
        movies = data.get("results", [])
        
        if not movies:
            await update.message.reply_text(
                f"🔍 No movies found for: {query}\n\n"
                "Try:\n"
                "• Different spelling\n"
                "• Original title\n"
                "• Year (e.g., 'Avengers 2019')\n"
                "• Partial title"
            )
            return
        
        # Show top 10 results
        results_text = f"🎬 Search Results for: {query}\n\n"
        
        keyboard = []
        
        for i, movie in enumerate(movies[:10], 1):
            title = movie.get("title", "Unknown Title")
            release_date = movie.get("release_date", "")
            year = f" ({release_date[:4]})" if release_date else ""
            overview = movie.get("overview", "No description available.")
            rating = movie.get("vote_average", 0)
            
            results_text += f"{i}. {title}{year}\n"
            results_text += f"⭐ Rating: {rating}/10\n"
            results_text += f"📝 {overview[:100]}{'...' if len(overview) > 100 else ''}\n\n"
            
            # Add download button for each movie
            keyboard.append([
                InlineKeyboardButton(
                    f"📥 Download {title[:30]}{'...' if len(title) > 30 else ''}",
                    callback_data=f"download_{movie['id']}"
                )
            ])
        
        results_text += f"Found {len(movies)} results (showing top 10)\n"
        results_text += f"Use download buttons or /download <movie_id>"
        
        # Add pagination if more results
        if len(movies) > 10:
            keyboard.append([
                InlineKeyboardButton("➡️ More Results", callback_data=f"search_page_2_{query}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            results_text,
            reply_markup=reply_markup
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"TMDB API error: {e}")
        await update.message.reply_text(
            "❌ Failed to search movies. Please try again later.\n"
            "The movie database service might be temporarily unavailable."
        )
    except Exception as e:
        logger.error(f"Movie search error: {e}")
        await update.message.reply_text(
            "❌ An error occurred while searching for movies.\n"
            "Please try again or contact support."
        )

async def download_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle movie download request"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /download <movie_id>\n\n"
            "Example: /download 299536\n"
            "Get movie ID from search results."
        )
        return
    
    try:
        movie_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid movie ID. Please provide a numeric ID.")
        return
    
    try:
        # Get movie details from TMDB
        details_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "append_to_response": "credits,videos,images"
        }
        
        response = requests.get(details_url, params=params, timeout=10)
        
        if response.status_code == 404:
            await update.message.reply_text("❌ Movie not found. Please check the movie ID.")
            return
        
        if response.status_code == 401:
            await update.message.reply_text(
                "❌ Movie service is currently unavailable.\n"
                "Please contact administrators."
            )
            return
        
        response.raise_for_status()
        movie = response.json()
        
        # Extract movie information
        title = movie.get("title", "Unknown Title")
        year = movie.get("release_date", "")[:4] if movie.get("release_date") else "Unknown"
        runtime = movie.get("runtime", 0)
        rating = movie.get("vote_average", 0)
        overview = movie.get("overview", "No description available.")
        genres = [g["name"] for g in movie.get("genres", [])]
        poster_path = movie.get("poster_path")
        
        # Get director and cast
        credits = movie.get("credits", {})
        crew = credits.get("crew", [])
        cast = credits.get("cast", [])
        
        director = next((person["name"] for person in crew if person["job"] == "Director"), "Unknown")
        main_cast = [actor["name"] for actor in cast[:5]]
        
        # Format movie details
        movie_details = f"""
🎬 {title} ({year})

⭐ Rating: {rating}/10
🎭 Genres: {', '.join(genres) if genres else 'N/A'}
🎯 Director: {director}
⏱️ Runtime: {runtime} minutes
👥 Cast: {', '.join(main_cast) if main_cast else 'N/A'}

📝 Overview:
{overview[:300]}{'...' if len(overview) > 300 else ''}

📥 Download Options:
"""
        
        # Generate download links (placeholder - implement actual download logic)
        download_options = [
            {"quality": "4K UHD", "size": "15-25 GB", "format": "MKV"},
            {"quality": "1080p", "size": "2-8 GB", "format": "MP4"},
            {"quality": "720p", "size": "1-3 GB", "format": "MP4"},
            {"quality": "480p", "size": "500MB-1GB", "format": "MP4"}
        ]
        
        keyboard = []
        
        for option in download_options:
            movie_details += f"• {option['quality']} ({option['size']}) - {option['format']}\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"📥 {option['quality']} ({option['size']})",
                    callback_data=f"dl_{movie_id}_{option['quality'].lower().replace(' ', '_')}"
                )
            ])
        
        movie_details += f"""
⚠️ Important Notes:
• Downloads are for personal use only
• Respect copyright laws in your country
• Support creators by watching legally when possible
• Large files may take time to generate

🔗 Legal Alternatives:
• Netflix, Amazon Prime, Disney+
• Rent/Buy on Google Play, iTunes
• Check local streaming services
        """
        
        # Add additional buttons
        keyboard.extend([
            [InlineKeyboardButton("🎥 Trailer", callback_data=f"trailer_{movie_id}"),
             InlineKeyboardButton("📊 More Info", callback_data=f"info_{movie_id}")],
            [InlineKeyboardButton("🔍 Similar Movies", callback_data=f"similar_{movie_id}"),
             InlineKeyboardButton("❌ Cancel", callback_data="cancel_download")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send movie poster if available
        if poster_path:
            poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
            try:
                await update.message.reply_photo(
                    photo=poster_url,
                    caption=movie_details,
                    reply_markup=reply_markup
                )
            except Exception:
                # Fallback to text if image fails
                await update.message.reply_text(
                    movie_details,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                movie_details,
                reply_markup=reply_markup
            )
        
        # Log download request
        user = update.effective_user
        logger.info(f"Download request: User {user.id} requested {title} ({year})")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"TMDB API error in download: {e}")
        await update.message.reply_text(
            "❌ Failed to get movie details. Please try again later.\n"
            "The movie database service might be temporarily unavailable."
        )
    except Exception as e:
        logger.error(f"Movie download error: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your download request.\n"
            "Please try again or contact support."
        )

async def get_movie_trailer(movie_id):
    """Get movie trailer from TMDB"""
    try:
        videos_url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US"
        }
        
        response = requests.get(videos_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        videos = data.get("results", [])
        
        # Find YouTube trailer
        for video in videos:
            if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                return f"https://www.youtube.com/watch?v={video['key']}"
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting trailer: {e}")
        return None

async def get_similar_movies(movie_id):
    """Get similar movies from TMDB"""
    try:
        similar_url = f"{TMDB_BASE_URL}/movie/{movie_id}/similar"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "page": 1
        }
        
        response = requests.get(similar_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data.get("results", [])[:10]
        
    except Exception as e:
        logger.error(f"Error getting similar movies: {e}")
        return []
