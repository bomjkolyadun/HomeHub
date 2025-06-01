"""
Utilities for video processing and file operations
"""
import os
import re
import subprocess
import urllib.parse

def is_problematic_filename(filename):
    """
    Check if a filename might cause issues with URL encoding
    
    Args:
        filename (str): The filename to check
        
    Returns:
        bool: True if the filename might cause issues, False otherwise
    """
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

def generate_thumbnail(video_rel_path, root_dir, thumb_dir):
    """
    Generate a thumbnail for a video if it doesn't exist
    
    Args:
        video_rel_path (str): Relative path to the video file from ROOT_DIR
        root_dir (str): The root directory for videos
        thumb_dir (str): The directory to store thumbnails
        
    Returns:
        str: The filename of the thumbnail
    """
    safe_name = video_rel_path.replace("/", "_").replace(" ", "_")
    full_path = os.path.join(root_dir, video_rel_path)
    thumb_path = os.path.join(thumb_dir, f"{safe_name}.jpg")
    
    if not os.path.exists(thumb_path):
        print(f"Generating thumbnail for {video_rel_path}")
        subprocess.run([
            "ffmpeg", "-ss", "00:00:02", "-i", full_path,
            "-vframes", "1", "-q:v", "2", thumb_path
        ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    
    return f"{safe_name}.jpg"

def decode_filename(filename):
    """
    Safely decode URL-encoded filename
    
    Args:
        filename (str): The filename to decode
    
    Returns:
        str: The decoded filename
    """
    try:
        return urllib.parse.unquote(filename)
    except Exception as e:
        print(f"Error decoding filename {filename}: {e}")
        return filename
