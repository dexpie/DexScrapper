import aiohttp
import aiofiles
import os
import logging
from urllib.parse import urlparse
import mimetypes

logger = logging.getLogger(__name__)

async def download_file(session, url, folder):
    """
    Downloads a file from a URL to a specified folder asynchronously.
    """
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                # Determine filename
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = "downloaded_file"
                    # Try to guess extension
                    content_type = response.headers.get('content-type')
                    ext = mimetypes.guess_extension(content_type)
                    if ext:
                        filename += ext

                filepath = os.path.join(folder, filename)
                
                # Write file
                async with aiofiles.open(filepath, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        await f.write(chunk)
                
                logger.info(f"Downloaded media: {filepath}")
                return filepath
    except Exception as e:
        logger.error(f"Failed to download media {url}: {e}")
    return None
