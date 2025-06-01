from flask import Flask, send_from_directory, render_template, abort, request
import os
import subprocess
import math
import time
import urllib.parse
import re

app = Flask(__name__)
ROOT_DIR = os.path.abspath("../vids")
THUMB_DIR = os.path.join(os.path.dirname(__file__), "thumbnails")
os.makedirs(THUMB_DIR, exist_ok=True)

# ffmpeg supported video formats
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.mkv', '.avi','.m4v', '.webm', '.flv', '.wmv')
VIDEOS_PER_PAGE = 10  # Number of videos to display per page

# Cache for video list and folders
VIDEOS_CACHE = {
    'last_updated': 0,
    'videos': [],
    'folders': [],
    'cache_ttl': 300  # Cache time-to-live in seconds (5 minutes)
}

# Check if a filename might cause issues with URL encoding
def is_problematic_filename(filename):
    # Characters that often cause issues when URL-encoded
    problematic_chars = ['%', '&', '+', ' ', '?', '#', '=', ';', ':', '@', '$', ',', '<', '>', '{', '}', '|', '\\', '^', '~', '[', ']', '`']
    
    # Check if any problematic character exists in the filename
    for char in problematic_chars:
        if char in filename:
            return True
            
    # Check if the filename is already URL-encoded (contains %)
    if '%' in filename and re.search(r'%[0-9A-Fa-f]{2}', filename):
        return True
        
    return False

# Get top-level folders
def get_folders(force_refresh=False):
    current_time = time.time()
    
    # Check if cache is valid
    if (not force_refresh and 
        VIDEOS_CACHE['folders'] and 
        current_time - VIDEOS_CACHE['last_updated'] < VIDEOS_CACHE['cache_ttl']):
        # Use cached folders
        return VIDEOS_CACHE['folders']
    
    # Find all top-level directories
    folders = ['']  # Include root directory
    for item in os.listdir(ROOT_DIR):
        item_path = os.path.join(ROOT_DIR, item)
        if os.path.isdir(item_path):
            folders.append(item)
    
    # Sort folders alphabetically 
    folders.sort()
    
    # Update cache
    VIDEOS_CACHE['folders'] = folders
    
    return folders

# Generate thumbnail for a video
def generate_thumbnail(video_rel_path):
    safe_name = video_rel_path.replace("/", "_").replace(" ", "_")
    full_path = os.path.join(ROOT_DIR, video_rel_path)
    thumb_path = os.path.join(THUMB_DIR, f"{safe_name}.jpg")
    
    if not os.path.exists(thumb_path):
        print(f"Generating thumbnail for {video_rel_path}")
        subprocess.run([
            "ffmpeg", "-ss", "00:00:02", "-i", full_path,
            "-vframes", "1", "-q:v", "2", thumb_path
        ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    
    return f"{safe_name}.jpg"

# Discover all videos with caching
def find_videos(folder='', force_refresh=False):
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
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            if f.lower().endswith(VIDEO_EXTENSIONS):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, ROOT_DIR)
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
        # Return videos in the root directory (no slash in path)
        return [v for v in videos if '/' not in v['rel_path']]

# Get paginated videos with lazy thumbnail generation
def get_paginated_videos(page=1, folder=''):
    all_videos = find_videos(folder=folder)
    total_videos = len(all_videos)
    total_pages = math.ceil(total_videos / VIDEOS_PER_PAGE) if total_videos > 0 else 1
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages))
    
    # Calculate start and end indices
    start_idx = (page - 1) * VIDEOS_PER_PAGE
    end_idx = min(start_idx + VIDEOS_PER_PAGE, total_videos)
    
    # Get videos for current page
    paginated_videos = all_videos[start_idx:end_idx] if total_videos > 0 else []
    
    # Generate thumbnails only for videos on the current page
    for video in paginated_videos:
        video['thumb'] = generate_thumbnail(video['rel_path'])
    
    return {
        'videos': paginated_videos,
        'current_page': page,
        'total_pages': total_pages,
        'total_videos': total_videos,
        'current_folder': folder
    }

@app.route("/")
@app.route("/folder/<path:folder>")
def index(folder=''):
    page = request.args.get('page', 1, type=int)
    pagination_data = get_paginated_videos(page, folder)
    folders = get_folders()
    
    return render_template(
        "video_template.html",
        videos=pagination_data['videos'],
        current_page=pagination_data['current_page'],
        total_pages=pagination_data['total_pages'],
        total_videos=pagination_data['total_videos'],
        current_folder=pagination_data['current_folder'],
        folders=folders
    )

@app.route("/video/<path:filename>")
def stream_video(filename):
    # Handle both URL-encoded and normal filenames
    try:
        # First try with the filename as-is
        return send_from_directory(ROOT_DIR, filename)
    except:
        try:
            # Try with URL decoding in case it's double-encoded
            decoded_filename = urllib.parse.unquote(filename)
            return send_from_directory(ROOT_DIR, decoded_filename)
        except Exception as e:
            print(f"Error accessing file: {filename}, Error: {str(e)}")
            abort(404)

@app.route("/thumb/<path:filename>")
def get_thumb(filename):
    return send_from_directory(THUMB_DIR, filename)

@app.route("/refresh")
def refresh_cache():
    find_videos(force_refresh=True)
    get_folders(force_refresh=True)
    return "Video cache refreshed! <a href='/'>Back to videos</a>"

if __name__ == "__main__":
    # Initial cache population
    find_videos(force_refresh=True)
    get_folders(force_refresh=True)
    app.run(host="0.0.0.0", port=8082)  # Changed port to 8082
