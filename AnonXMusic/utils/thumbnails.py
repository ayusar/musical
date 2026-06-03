from config import YOUTUBE_IMG_URL

async def get_thumb(videoid, user_id):
    """
    Return direct YouTube thumbnail URL without downloading any file.
    No disk I/O, no cache storage.
    """
    # YouTube official thumbnail URL (high quality)
    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    
    # Directly return the URL – no download, no cache.
    # The bot will use this URL directly in send_photo/reply_photo.
    return thumb_url
