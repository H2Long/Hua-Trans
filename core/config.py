"""Configuration management for TranslateTor."""

import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "hotkey": "ctrl+shift+t",
    "source_lang": "en",
    "target_lang": "zh",
    "translation_engine": "google",  # google, deepl, llm
    "deepl_api_key": "",
    "llm_api_key": "",
    "llm_model": "claude-sonnet-4-20250514",
    "llm_base_url": "https://api.anthropic.com",
    "ocr_language": "eng",
    "theme": "deep_purple_blue",
    "font_size": 14,
    "popup_width": 450,
    "popup_height": 300,
    "popup_opacity": 0.95,
    "popup_mini_mode": False,
    "popup_position": None,  # {"x": int, "y": int}, set when user drags the popup
    "auto_hide_seconds": 0,  # 0 = never auto-hide, stay until manually closed
    "cache_enabled": True,
    "cache_max_days": 30,
    "terminology_highlight": True,
    "page_shortcuts": {"translation": "Ctrl+1", "history": "Ctrl+2", "terminology": "Ctrl+3", "settings": "Ctrl+4"},
    "window_geometry": None,
    "window_state": None,
    "last_page": 0,
}

CONFIG_DIR = Path.home() / ".translatetor"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"
TERMS_FILE = CONFIG_DIR / "terms.json"


def ensure_dirs():
    """Ensure configuration directories exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file, creating defaults if needed."""
    ensure_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(saved)
            return config
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Save configuration to file."""
    ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
