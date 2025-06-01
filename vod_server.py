from flask import Flask, send_from_directory, render_template, abort, request
import os
import subprocess
import math
import time

app = Flask(__name__)
ROOT_DIR = os.path.abspath("../vids")
THUMB_DIR = os.path.join(os.path.dirname(__file__), "thumbnails")
os.makedirs(THUMB_DIR, exist_ok=True)

VIDEO_EXTENSIONS = ('.mp4', '.mov', '.mkv', '.avi')
VIDEOS_PER_PAGE = 10  # Number of videos to display per page

# Cache for video list and folders
VIDEOS_CACHE = {
    'last_updated': 0,
    'videos': [],
    'folders': [],
    'cache_ttl': 300  # Cache time-to-live in seconds (5 minutes)
}

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
def find_videos(force_refresh=False):
    current_time = time.time()
    
    # Check if cache is valid
    if (not force_refresh and 
        VIDEOS_CACHE['videos'] and 
        current_time - VIDEOS_CACHE['last_updated'] < VIDEOS_CACHE['cache_ttl']):
        # Use cached videos
        return VIDEOS_CACHE['videos']
    
    # Cache expired or forced refresh, rebuild video list
    print("Refreshing video cache...")
    videos = []
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            if f.lower().endswith(VIDEO_EXTENSIONS):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, ROOT_DIR)
                safe_name = rel_path.replace("/", "_").replace(" ", "_")
                
                videos.append({
                    'rel_path': rel_path,
                    'thumb': f"{safe_name}.jpg"
                })
    
    # Update cache
    VIDEOS_CACHE['videos'] = videos
    VIDEOS_CACHE['last_updated'] = current_time
    
    return videos

# Get paginated videos with lazy thumbnail generation
def get_paginated_videos(page=1):
    all_videos = find_videos()
    total_videos = len(all_videos)
    total_pages = math.ceil(total_videos / VIDEOS_PER_PAGE)
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    # Calculate start and end indices
    start_idx = (page - 1) * VIDEOS_PER_PAGE
    end_idx = min(start_idx + VIDEOS_PER_PAGE, total_videos)
    
    # Get videos for current page
    paginated_videos = all_videos[start_idx:end_idx]
    
    # Generate thumbnails only for videos on the current page
    for video in paginated_videos:
        video['thumb'] = generate_thumbnail(video['rel_path'])
    
    return {
        'videos': paginated_videos,
        'current_page': page,
        'total_pages': total_pages,
        'total_videos': total_videos
    }

@app.route("/")
def index():
    page = request.args.get('page', 1, type=int)
    pagination_data = get_paginated_videos(page)
    return render_template(
        "video_template.html",
        videos=pagination_data['videos'],
        current_page=pagination_data['current_page'],
        total_pages=pagination_data['total_pages'],
        total_videos=pagination_data['total_videos']
    )

@app.route("/video/<path:filename>")
def stream_video(filename):
    return send_from_directory(ROOT_DIR, filename)

@app.route("/thumb/<path:filename>")
def get_thumb(filename):
    return send_from_directory(THUMB_DIR, filename)

@app.route("/refresh")
def refresh_cache():
    find_videos(force_refresh=True)
    return "Video cache refreshed! <a href='/'>Back to videos</a>"

if __name__ == "__main__":
    # Initial cache population
    find_videos(force_refresh=True)
    app.run(host="0.0.0.0", port=8082)  # Changed port to 8082
