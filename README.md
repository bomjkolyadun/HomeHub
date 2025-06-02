# Video-on-Demand (VOD) Server

A Flask-based Video-on-Demand server with responsive UI, folder navigation, pagination, and flexible configuration.

## Features

- Responsive mobile-friendly UI
- Video pagination with configurable items per page
- Folder navigation with sidebar
- URL-encoded video streaming
- Thumbnail generation
- Configuration system with defaults and overrides
- Warning system for problematic filenames
- Caching mechanism for directory scanning

## Configuration System

The server uses Flask's configuration system with support for defaults and environment-specific overrides. Configuration is handled in Python files rather than JSON.

### Default Configuration

The default configuration is defined in `app/default_config.py`:

```python
DEFAULT_VOD_CONFIG = {
    "server": {
        "port": 8080,
        "host": "0.0.0.0",
        "debug": False
    },
    "directories": {
        "videos": "../vids",
        "web_assets": "../www"
    },
    "video": {
        "extensions": [".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".flv", ".wmv"],
        "per_page": 10
    },
    "cache": {
        "ttl_seconds": 300
    }
}
```

### Instance Configuration

Following Flask best practices, instance-specific configurations are stored in the `instance/` folder:

1. **Base Instance Configuration** - `instance/config.py`:

   ```python
   # Flask configuration
   SECRET_KEY = "your-secret-key-here"  # Change this in production!
   
   # Homehub Configuration
   VOD_CONFIG = {
       "server": {
           "port": 8082,
           "host": "0.0.0.0",
           "debug": False
       },
       # Only include settings you want to override
   }
   ```

2. **Environment-specific Configuration** - `instance/config.development.py`:

   ```python
   # Development configuration
   SECRET_KEY = "dev-secret-key"
   
   VOD_CONFIG = {
       "server": {
           "port": 5000,
           "host": "127.0.0.1",
           "debug": True
       },
       "cache": {
           "ttl_seconds": 30  # Short cache for development
       }
   }
   ```

Only settings you want to override need to be included. Any settings not specified will fall back to the defaults.


## Usage

### Starting the server

With default configuration (production):

```bash
python run.py
```

With development configuration (loads `instance/config.development.py`):

```bash
python run.py -e development
```

You can create or edit `instance/config.py` and `instance/config.development.py` to override any settings for your environment.

## Architecture

The server follows a standard Flask application structure:

- `run.py`: Application entry point
- `app/`: Main application package
  - `__init__.py`: Flask app initialization
  - `routes.py`: Route definitions and handlers
  - `config.py`: Configuration management
  - `utils/`: Utility modules
    - `video_utils.py`: Video processing utilities
    - `cache_manager.py`: Cache management and video listing
  - `templates/`: HTML templates
  - `static/`: Static assets (CSS, JS, etc.)
- `instance/`: Instance-specific config (excluded from version control)

## Browser Access

Once running, access the server in your web browser:

- Default URL: `http://localhost:8082/`
- Replace 8082 with your configured port
