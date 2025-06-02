"""
Cache management and video listing functionality
"""
import os
import time
import urllib.parse
import math
from app.utils.video_utils import is_problematic_filename, generate_thumbnail

# Cache data structure
VIDEOS_CACHE = {
    'last_updated': 0,
    'videos': [],
    'folders': [],
    'cache_ttl': 300  # Default TTL, will be updated from config
}

def init_cache(config):
    """
    Initialize the cache with configuration
    
    Args:
        config (dict): The configuration dictionary
    """
    global VIDEOS_CACHE
    VIDEOS_CACHE['cache_ttl'] = config['cache']['ttl_seconds']

def get_folders(root_dir, force_refresh=False):
    """
    Get top-level folders
    
    Args:
        root_dir (str): The root directory for videos
        force_refresh (bool): Whether to force a refresh of the cache
        
    Returns:
        list: List of folder names
    """
    current_time = time.time()
    
    # Check if cache is valid
    if (not force_refresh and 
        VIDEOS_CACHE['folders'] and 
        current_time - VIDEOS_CACHE['last_updated'] < VIDEOS_CACHE['cache_ttl']):
        # Use cached folders
        return VIDEOS_CACHE['folders']
    
    # Find all top-level directories
    folders = ['']  # Include root directory
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path):
            folders.append(item)
    
    # Sort folders alphabetically 
    folders.sort()
    
    # Update cache
    VIDEOS_CACHE['folders'] = folders
    
    return folders

def find_videos(root_dir, video_extensions, folder='', force_refresh=False):
    """
    Discover all videos with caching
    
    Args:
        root_dir (str): The root directory for videos
        video_extensions (tuple): Supported video file extensions
        folder (str): The folder to filter by
        force_refresh (bool): Whether to force a refresh of the cache
        
    Returns:
        list: List of video dictionaries
    """
    current_time = time.time()
    
    # Check if cache is valid
    if (not force_refresh and 
        VIDEOS_CACHE['videos'] and 
        current_time - VIDEOS_CACHE['last_updated'] < VIDEOS_CACHE['cache_ttl']):
        # Use cached videos, but filter by folder
        all_videos = VIDEOS_CACHE['videos']
        
        if folder:
            # Filter videos in the specified folder
            return [v for v in all_videos if v['rel_path'].startswith(f"{folder}/")]
        else:
            # Return videos in the root directory (no slash in path)
            return all_videos
    
    # Cache expired or forced refresh, rebuild video list
    print("Refreshing video cache...")
    videos = []
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(video_extensions):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, root_dir)
                safe_name = rel_path.replace("/", "_").replace(" ", "_")
                
                # Check if this filename might cause issues
                filename = os.path.basename(rel_path)
                has_issue = is_problematic_filename(filename)
                
                videos.append({
                    'rel_path': rel_path,
                    'thumb': f"{safe_name}.jpg",
                    'filename': filename,
                    'has_issue': has_issue,
                    'encoded_path': urllib.parse.quote(rel_path)
                })
    
    # Update cache
    VIDEOS_CACHE['videos'] = videos
    VIDEOS_CACHE['last_updated'] = current_time
    
    # Filter by folder
    if folder:
        # Filter videos in the specified folder
        return [v for v in videos if v['rel_path'].startswith(f"{folder}/")]
    else:
        # Return all videos (Home page)
        return videos

def get_paginated_videos(root_dir, thumb_dir, videos_per_page, video_extensions, page=1, folder=''):
    """
    Get paginated videos with lazy thumbnail generation
    
    Args:
        root_dir (str): The root directory for videos
        thumb_dir (str): The directory to store thumbnails
        videos_per_page (int): Number of videos per page
        video_extensions (tuple): Supported video file extensions
        page (int): The page number
        folder (str): The folder to filter by
        
    Returns:
        dict: Pagination data including videos and pagination info
    """
    all_videos = find_videos(root_dir, video_extensions, folder=folder)
    total_videos = len(all_videos)
    total_pages = math.ceil(total_videos / videos_per_page) if total_videos > 0 else 1
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages))
    
    # Calculate start and end indices
    start_idx = (page - 1) * videos_per_page
    end_idx = min(start_idx + videos_per_page, total_videos)
    
    # Get videos for current page
    paginated_videos = all_videos[start_idx:end_idx] if total_videos > 0 else []
    
    # Generate thumbnails only for videos on the current page
    for video in paginated_videos:
        video['thumb'] = generate_thumbnail(video['rel_path'], root_dir, thumb_dir)
    
    return {
        'videos': paginated_videos,
        'current_page': page,
        'total_pages': total_pages,
        'total_videos': total_videos,
        'current_folder': folder
    }
