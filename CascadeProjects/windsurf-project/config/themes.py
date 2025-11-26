"""
Predefined themes for MQTT Dashboard widgets
Inspired by Grafana's modern design system
"""

PREDEFINED_THEMES = {
    "grafana_dark": {
        "name": "Grafana Dark",
        "description": "Dark theme inspired by Grafana's default dark mode",
        "colors": {
            "background": "#181B1F",
            "surface": "#1F2428", 
            "primary": "#FF9830",
            "secondary": "#73BF69",
            "accent": "#6E9FFF",
            "text": "#D9D9D9",
            "text_secondary": "#8E8E8E",
            "border": "#2F3338",
            "success": "#73BF69",
            "warning": "#FF9830", 
            "error": "#F2495C",
            "info": "#6E9FFF"
        }
    },
    
    "grafana_light": {
        "name": "Grafana Light", 
        "description": "Light theme inspired by Grafana's light mode",
        "colors": {
            "background": "#F7F8FA",
            "surface": "#FFFFFF",
            "primary": "#FF6600",
            "secondary": "#52C41A",
            "accent": "#1890FF",
            "text": "#141619",
            "text_secondary": "#6C6C6C",
            "border": "#E6E6E6",
            "success": "#52C41A",
            "warning": "#FF6600",
            "error": "#FF4D4F", 
            "info": "#1890FF"
        }
    },
    
    "grafana_blue": {
        "name": "Grafana Blue",
        "description": "Blue-themed dark variant with modern gradients",
        "colors": {
            "background": "#0B1426",
            "surface": "#111927",
            "primary": "#3274D9",
            "secondary": "#5794F2", 
            "accent": "#8AB8FF",
            "text": "#D9D9D9",
            "text_secondary": "#9FA7B3",
            "border": "#1F2937",
            "success": "#73BF69",
            "warning": "#FF9830",
            "error": "#F2495C",
            "info": "#5794F2"
        }
    },
    
    "modern_purple": {
        "name": "Modern Purple",
        "description": "Contemporary purple theme with high contrast",
        "colors": {
            "background": "#1A1625",
            "surface": "#252138",
            "primary": "#8B5CF6",
            "secondary": "#A78BFA",
            "accent": "#C4B5FD",
            "text": "#F3F4F6",
            "text_secondary": "#9CA3AF",
            "border": "#374151",
            "success": "#10B981",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "info": "#3B82F6"
        }
    },
    
    "cyberpunk": {
        "name": "Cyberpunk",
        "description": "Futuristic neon-inspired theme",
        "colors": {
            "background": "#0A0A0F",
            "surface": "#1A1A2E",
            "primary": "#00F5FF",
            "secondary": "#FF073A",
            "accent": "#39FF14",
            "text": "#FFFFFF",
            "text_secondary": "#B0B0B0",
            "border": "#16213E",
            "success": "#39FF14",
            "warning": "#FFD700",
            "error": "#FF073A",
            "info": "#00F5FF"
        }
    },
    
    "minimal_gray": {
        "name": "Minimal Gray",
        "description": "Clean minimal theme with subtle grays",
        "colors": {
            "background": "#FAFAFA",
            "surface": "#FFFFFF",
            "primary": "#2563EB",
            "secondary": "#64748B",
            "accent": "#0EA5E9",
            "text": "#0F172A",
            "text_secondary": "#64748B",
            "border": "#E2E8F0",
            "success": "#059669",
            "warning": "#D97706",
            "error": "#DC2626",
            "info": "#2563EB"
        }
    }
}

# Start with predefined themes, custom themes will be added at runtime
THEMES = PREDEFINED_THEMES.copy()

def load_custom_themes():
    """Load custom themes from settings"""
    from config.settings import load_settings
    settings = load_settings()
    custom_themes = settings.get('custom_themes', {})
    THEMES.update(custom_themes)
    return custom_themes

def save_custom_theme(theme_key, theme_data):
    """Save a custom theme to settings"""
    from config.settings import load_settings, save_settings
    settings = load_settings()
    if 'custom_themes' not in settings:
        settings['custom_themes'] = {}
    settings['custom_themes'][theme_key] = theme_data
    save_settings(settings)
    THEMES[theme_key] = theme_data

def delete_custom_theme(theme_key):
    """Delete a custom theme"""
    from config.settings import load_settings, save_settings
    settings = load_settings()
    if 'custom_themes' in settings and theme_key in settings['custom_themes']:
        del settings['custom_themes'][theme_key]
        save_settings(settings)
        if theme_key in THEMES:
            del THEMES[theme_key]

def get_theme_config(theme_key, widget_type):
    """Get theme configuration for a specific widget type"""
    if theme_key not in THEMES:
        return {}
    
    theme = THEMES[theme_key]
    
    # Base configuration for all widgets
    config = {
        'bg_color': theme['colors']['surface'],
        'text_color': theme['colors']['text'],
        'border_color': theme['colors']['border'],
        'accent_color': theme['colors']['accent']
    }
    
    # Widget-specific configurations
    if widget_type == 'gauge':
        config.update({
            'normal_zone_color': theme['colors']['info'],
            'warning_color': theme['colors']['warning'],
            'critical_color': theme['colors']['error']
        })
    elif widget_type == 'button':
        config.update({
            'accent_color': theme['colors']['accent']
        })
    elif widget_type == 'slider':
        config.update({
            'accent_color': theme['colors']['accent']
        })
    elif widget_type == 'app':
        # Main application theme
        config.update({
            'sidebar_bg': theme['colors']['secondary'],
            'panel_bg': theme['colors']['background'],
            'hover_color': theme['colors']['accent'] + '22',  # Semi-transparent accent
            'active_color': theme['colors']['accent']
        })
    
    return config

def get_theme_list():
    """Get list of available themes (predefined and custom)"""
    return [(key, theme["name"], theme["description"])
            for key, theme in THEMES.items()]

def apply_theme_to_dashboard(dashboard_widget, theme_name):
    """Apply theme to dashboard background"""
    if theme_name not in THEMES:
        return

    theme = THEMES[theme_name]
    colors = theme["colors"]
    
    # Apply dashboard background
    dashboard_widget.setStyleSheet(f"""
        QWidget {{
            background-color: {colors["background"]};
            color: {colors["text"]};
        }}
        QScrollArea {{
            background-color: {colors["background"]};
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: {colors["background"]};
        }}
    """)
