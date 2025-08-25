"""
URL shortening functionality using mraprguilds.site
"""

import logging
import asyncio
import aiohttp
from urllib.parse import quote

from .config import SHORTENER_URL, SHORTENER_API_KEY

logger = logging.getLogger(__name__)

async def shorten_url(long_url: str) -> str:
    """
    Shorten a URL using mraprguilds.site service
    """
    try:
        # If no API key available, return original URL
        if not SHORTENER_API_KEY:
            logger.warning("No shortener API key available, returning original URL")
            return long_url
        
        # Prepare the API request
        api_endpoint = f"{SHORTENER_URL}/api?api/shorten"
        headers = {
            'Authorization': f'Bearer {SHORTENER_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'url': long_url,
            'custom_alias': None,  # Auto-generate alias
            'expiry_days': 365     # Link expires in 1 year
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    shortened_url = data.get('shortened_url')
                    
                    if shortened_url:
                        logger.info(f"URL shortened successfully: {long_url[:50]}... -> {shortened_url}")
                        return shortened_url
                    else:
                        logger.error("No shortened URL in response")
                        return long_url
                
                else:
                    logger.error(f"URL shortening failed with status {response.status}")
                    return long_url
    
    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        return long_url

async def get_url_stats(short_url: str) -> dict:
    """
    Get statistics for a shortened URL
    """
    try:
        if not SHORTENER_API_KEY:
            return {}
        
        # Extract the short code from the URL
        if SHORTENER_URL in short_url:
            short_code = short_url.split('/')[-1]
        else:
            return {}
        
        api_endpoint = f"{SHORTENER_URL}/api?api/stats/{short_code}"
        headers = {
            'Authorization': f'Bearer {SHORTENER_API_KEY}',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_endpoint, headers=headers) as response:
                if response.status == 200:
                    stats = await response.json()
                    logger.info(f"Retrieved stats for {short_url}")
                    return stats
                else:
                    logger.error(f"Failed to get URL stats with status {response.status}")
                    return {}
    
    except Exception as e:
        logger.error(f"Error getting URL stats: {e}")
        return {}

async def create_custom_short_url(long_url: str, custom_alias: str) -> str:
    """
    Create a custom shortened URL with specific alias
    """
    try:
        if not SHORTENER_API_KEY:
            logger.warning("No shortener API key available, returning original URL")
            return long_url
        
        api_endpoint = f"{SHORTENER_URL}/api?api/shorten"
        headers = {
            'Authorization': f'Bearer {SHORTENER_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'url': long_url,
            'custom_alias': custom_alias,
            'expiry_days': 365
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    shortened_url = data.get('shortened_url')
                    
                    if shortened_url:
                        logger.info(f"Custom URL created: {custom_alias} -> {shortened_url}")
                        return shortened_url
                    else:
                        return long_url
                
                elif response.status == 409:  # Alias already exists
                    logger.warning(f"Custom alias '{custom_alias}' already exists")
                    # Fall back to auto-generated alias
                    return await shorten_url(long_url)
                
                else:
                    logger.error(f"Custom URL creation failed with status {response.status}")
                    return long_url
    
    except Exception as e:
        logger.error(f"Error creating custom short URL: {e}")
        return long_url

def generate_qr_code_url(url: str) -> str:
    """
    Generate QR code URL for a given URL
    """
    try:
        # Use a free QR code service
        qr_api = "https://api.qrserver.com/v1/create-qr-code/"
        encoded_url = quote(url)
        qr_url = f"{qr_api}?size=300x300&data={encoded_url}"
        
        logger.info(f"Generated QR code URL for: {url[:50]}...")
        return qr_url
    
    except Exception as e:
        logger.error(f"Error generating QR code URL: {e}")
        return ""

async def bulk_shorten_urls(urls: list) -> dict:
    """
    Shorten multiple URLs at once
    """
    try:
        if not SHORTENER_API_KEY:
            logger.warning("No shortener API key available")
            return {url: url for url in urls}  # Return original URLs
        
        results = {}
        
        # Process URLs concurrently
        tasks = []
        for url in urls:
            task = asyncio.create_task(shorten_url(url))
            tasks.append((url, task))
        
        # Wait for all tasks to complete
        for original_url, task in tasks:
            try:
                shortened_url = await task
                results[original_url] = shortened_url
            except Exception as e:
                logger.error(f"Error shortening {original_url}: {e}")
                results[original_url] = original_url
        
        logger.info(f"Bulk shortened {len(results)} URLs")
        return results
    
    except Exception as e:
        logger.error(f"Error in bulk URL shortening: {e}")
        return {url: url for url in urls}

def is_shortened_url(url: str) -> bool:
    """
    Check if a URL is a shortened URL from our service
    """
    return SHORTENER_URL.replace('https://', '').replace('http://', '') in url

async def expand_url(short_url: str) -> str:
    """
    Expand a shortened URL to get the original URL
    """
    try:
        if not is_shortened_url(short_url):
            return short_url
        
        # For security, we'll just return the short URL
        # In production, you might want to implement expansion
        logger.info(f"URL expansion requested for: {short_url}")
        return short_url
    
    except Exception as e:
        logger.error(f"Error expanding URL: {e}")
        return short_url
