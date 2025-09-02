import os
import json
from pathlib import Path

def get_config_path():
    """Get the path to the config directory"""
    config_dir = os.path.join(str(Path.home()), ".config", "mqtt-dashboard")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "settings.json")

def load_settings():
    """Load settings from config file"""
    config_file = get_config_path()
    if not os.path.exists(config_file):
        return {
            'broker': 'localhost',
            'port': 1883,
            'username': '',
            'password': '',
            'use_ssl': False,
            'auto_connect': False,
            'dashboard': {
                'theme': 'light',
                'font_size': 12,
                'recent_files': []
            }
        }
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return {}

def save_settings(settings):
    """Save settings to config file"""
    try:
        config_file = get_config_path()
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def get_setting(key, default=None):
    """Get a specific setting value"""
    settings = load_settings()
    return settings.get(key, default)

def set_setting(key, value):
    """Set a specific setting value"""
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)
