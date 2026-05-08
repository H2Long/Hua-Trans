"""Configuration management for TranslateTor.

API keys (deepl_api_key, llm_api_key) are stored in the OS keychain
via keyring. Plaintext keys in config.json are migrated on first load.
"""

import json
import os
import sys
from pathlib import Path

try:
    import keyring as _keyring
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False

_KEYRING_SERVICE = "hua-trans"
_KEYRING_KEYS = {
    "deepl_api_key": "deepl_api_key",
    "llm_api_key": "llm_api_key",
}
_SENSITIVE_KEYS = frozenset(_KEYRING_KEYS.keys())

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
    "overlay_stagger_ms": 50,  # ms between follow-up overlay translation requests
    "overlay_concurrent": 5,  # max simultaneous overlay translation workers
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


def _migrate_keys_to_keyring(config: dict):
    """Move plaintext API keys from config dict into OS keychain."""
    if not _KEYRING_AVAILABLE:
        return
    dirty = False
    for key_name in _SENSITIVE_KEYS:
        value = config.get(key_name, "")
        if value:
            try:
                _keyring.set_password(_KEYRING_SERVICE, key_name, value)
                config[key_name] = ""
                dirty = True
            except Exception:
                pass  # Keyring may fail on headless systems; keep plaintext
    if dirty:
        save_config(config)


def load_config() -> dict:
    """Load configuration from file, creating defaults if needed.

    API keys are loaded from keyring and injected into the config dict.
    Plaintext keys in config.json are migrated to keyring on first load.
    """
    ensure_dirs()
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, IOError):
            pass

    # Migrate plaintext keys → keyring
    _migrate_keys_to_keyring(config)

    # Inject keys from keyring into config dict
    if _KEYRING_AVAILABLE:
        for key_name in _SENSITIVE_KEYS:
            try:
                value = _keyring.get_password(_KEYRING_SERVICE, key_name)
                if value:
                    config[key_name] = value
            except Exception:
                pass

    return config


def save_config(config: dict):
    """Save configuration to file, stripping sensitive keys."""
    ensure_dirs()
    safe = {k: v for k, v in config.items() if k not in _SENSITIVE_KEYS}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)


def store_api_key(key_name: str, value: str):
    """Store an API key in the OS keychain."""
    if not _KEYRING_AVAILABLE:
        return False
    try:
        _keyring.set_password(_KEYRING_SERVICE, key_name, value)
        return True
    except Exception:
        return False


def delete_api_key(key_name: str):
    """Delete an API key from the OS keychain."""
    if not _KEYRING_AVAILABLE:
        return False
    try:
        _keyring.delete_password(_KEYRING_SERVICE, key_name)
        return True
    except Exception:
        return False


def get_api_key(key_name: str) -> str:
    """Read an API key from the OS keychain."""
    if not _KEYRING_AVAILABLE:
        return ""
    try:
        return _keyring.get_password(_KEYRING_SERVICE, key_name) or ""
    except Exception:
        return ""
