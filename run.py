#!/usr/bin/env python3
"""
Homehub - Main entry point
"""
import os
import argparse
import sys
import shutil
from app import create_app

def main():
    """Main entry point for the application"""
    # Check for ffmpeg
    if shutil.which('ffmpeg') is None:
        print("ERROR: ffmpeg is not installed or not found in PATH. Please install ffmpeg to use this server.", file=sys.stderr)
        sys.exit(1)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Homehub')
    parser.add_argument('-e', '--env', help='Environment (development, production)', default='production')
    args = parser.parse_args()

    # Set Flask environment
    if args.env:
        os.environ['FLASK_ENV'] = args.env

    # Create Flask application
    app = create_app()

    # Use application context to access config
    with app.app_context():
        from app.config import get_config
        config = get_config()

        # Create necessary directories with error handling
        root_dir = os.path.abspath(config['directories']['videos'])
        web_assets_dir = os.path.abspath(config['directories']['web_assets'])
        thumb_dir = os.path.join(web_assets_dir, "thumbnails")

        try:
            os.makedirs(root_dir, exist_ok=True)
            os.makedirs(web_assets_dir, exist_ok=True)
            os.makedirs(thumb_dir, exist_ok=True)
        except OSError as e:
            print(f"ERROR: Unable to create required directories: {e}", file=sys.stderr)
            sys.exit(1)

        for path in (root_dir, web_assets_dir, thumb_dir):
            if not (os.access(path, os.R_OK) and os.access(path, os.W_OK)):
                print(f"ERROR: Insufficient permissions for directory {path}", file=sys.stderr)
                sys.exit(1)

        # Print server information
        print(f"Homehub Configuration:")
        print(f"- Environment: {os.environ.get('FLASK_ENV', 'production')}")
        print(f"- Videos directory: {root_dir}")
        print(f"- Web assets directory: {web_assets_dir}")
        print(f"- Supported extensions: {', '.join(config['video']['extensions'])}")
        print(f"- Videos per page: {config['video']['per_page']}")

        # Start the server
        app.run(
            host=config['server']['host'],
            port=config['server']['port'],
            debug=config['server']['debug']
        )

if __name__ == "__main__":
    main()
