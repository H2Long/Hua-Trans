"""TranslateTor - Universal Translation Tool with EE Terminology.

Main entry point. Handles hotkey registration, clipboard monitoring,
system tray, and launches the PyQt5 application.
"""

import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox,
)
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QIcon

from core.config import load_config, save_config
from core.terminology import TerminologyDB
from core.translator import TranslationManager
from core.cache import TranslationCache
from core.clipboard import ClipboardManager
from core.ocr_handler import OCRHandler
from core.hotkey_manager import HotkeyManager
from gui.theme import set_active_theme
from gui.main_window import MainWindow
from gui.floating_widget import FloatingTranslation


class HotkeyBridge(QObject):
    """Bridge between keyboard hotkey thread and Qt main thread."""
    triggered = pyqtSignal(dict)


def create_hotkey_callback(config, clipboard, bridge, floating,
                           translator, cache):
    """Create the callback function for the hotkey."""
    def on_hotkey():
        # Auto-copy: simulate Ctrl+C to grab selected text, then read clipboard
        text = clipboard.get_selected_text_via_copy()
        if not text:
            # Fallback: user may have already copied manually before pressing hotkey
            text = clipboard.get_text_and_restore()
        if not text:
            return

        engine = config.get("translation_engine", "google")
        cached = None
        if config.get("cache_enabled"):
            cached = cache.get(
                text, engine,
                config.get("source_lang", "en"),
                config.get("target_lang", "zh"),
            )
        if cached:
            result = {"original": text, "translated": cached, "engine": engine, "terms_applied": []}
        else:
            try:
                result = translator.translate(text, engine)
            except Exception as e:
                result = {"original": text, "translated": f"Error: {e}", "engine": engine, "terms_applied": []}

        bridge.triggered.emit(result)

    return on_hotkey


def _load_app_icon():
    """Load the application icon for tray and windows."""
    paths = [
        Path(__file__).parent / "resources" / "icon.png",
        Path.home() / ".translatetor" / "icon.png",
    ]
    for p in paths:
        if p.exists():
            return QIcon(str(p))
    # Fallback: use a built-in QStyle icon
    return QApplication.style().standardIcon(
        QApplication.style().SP_ComputerIcon
    )


def main():
    import signal as _signal

    # Enable input method support (Linux X11 only)
    if sys.platform == "linux":
        os.environ.setdefault("QT_IM_MODULE", "ibus")
        os.environ.setdefault("XMODIFIERS", "@im=ibus")

    # Handle Ctrl+C gracefully
    _signal.signal(_signal.SIGINT, lambda *_: QApplication.quit())

    # Load config
    config = load_config()

    # Apply theme
    set_active_theme(config.get("theme", "dark_professional"))

    # Initialize core modules
    terminology = TerminologyDB()
    translator = TranslationManager(config, terminology)
    cache = TranslationCache(max_days=config.get("cache_max_days", 30))
    clipboard = ClipboardManager()
    ocr = OCRHandler(language=config.get("ocr_language", "eng"))
    hotkey_mgr = HotkeyManager()

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("黄花梨之译")
    app.setApplicationDisplayName("黄花梨之译")
    # Don't quit when last window is hidden (tray stays alive)
    app.setQuitOnLastWindowClosed(False)

    # Load app icon
    app_icon = _load_app_icon()
    app.setWindowIcon(app_icon)

    # Create UI
    main_win = MainWindow(config, terminology, translator, cache, ocr)
    main_win.setWindowIcon(app_icon)
    floating = FloatingTranslation(config, available_engines=translator.get_available_engines())

    # -- System tray ----------------------------------------------------
    tray = QSystemTrayIcon(app_icon, app)
    tray.setToolTip("黄花梨之译")

    tray_menu = QMenu()

    show_action = QAction("显示主窗口", tray_menu)
    show_action.triggered.connect(lambda: _show_main_window(main_win))

    floating_action = QAction("触发悬浮翻译", tray_menu)
    floating_action.triggered.connect(lambda: _tray_floating_translate(
        clipboard, floating, translator, config, cache, main_win,
    ))

    tray_menu.addAction(show_action)
    tray_menu.addAction(floating_action)
    tray_menu.addSeparator()

    quit_action = QAction("退出", tray_menu)
    quit_action.triggered.connect(lambda: _quit_app(app, main_win, config, hotkey_mgr))
    tray_menu.addAction(quit_action)

    tray.setContextMenu(tray_menu)
    tray.activated.connect(lambda reason: _on_tray_activated(reason, main_win, floating,
                                                              clipboard, translator, config, cache))
    tray.show()

    # Minimize to tray instead of closing
    main_win._tray = tray
    main_win._app = app

    # Store usage tracker ref on main_win for status bar updates
    from core.usage_tracker import UsageTracker
    main_win._usage_tracker = UsageTracker.instance(str(cache.db_path))

    # Hotkey bridge — runs in main thread via queued signal
    bridge = HotkeyBridge()

    def on_hotkey_result(result: dict):
        """Handle hotkey translation result in the main thread."""
        floating.show_translation(
            result["original"], result["translated"],
            result["engine"], result.get("terms_applied"),
        )
        # Save to history cache
        if config.get("cache_enabled", True):
            cache.put(
                result["original"], result["translated"],
                result["engine"],
                config.get("source_lang", "en"),
                config.get("target_lang", "zh"),
            )
        # Track usage
        main_win._usage_tracker.record(
            result["engine"], len(result["original"]),
        )
        main_win.hotkey_translate.emit(result["translated"])

    bridge.triggered.connect(on_hotkey_result)

    # Connect hotkey signal to translation page
    main_win.hotkey_translate.connect(main_win.get_translation_page().on_hotkey_translate)

    # Create hotkey callback
    hotkey_callback = create_hotkey_callback(
        config, clipboard, bridge, floating, translator, cache,
    )

    # Register initial hotkey
    if hotkey_mgr.is_available():
        ok, msg = hotkey_mgr.register(config.get("hotkey", "ctrl+shift+t"), hotkey_callback)
        print(f"Hotkey: {msg}")
        main_win._sidebar.set_hotkey_status(ok)

        # Wire hotkey change from settings
        def on_hotkey_changed(new_hotkey):
            ok, msg = hotkey_mgr.register(new_hotkey, hotkey_callback)
            print(f"Hotkey change: {msg}")
            main_win._sidebar.set_hotkey_status(ok)

        main_win.get_settings_page().hotkey_changed.connect(on_hotkey_changed)
    else:
        print("Warning: python-xlib not available. Hotkey disabled.")
        print("  Install: pip install python-xlib")
        main_win._sidebar.set_hotkey_status(False)

    # Show main window
    main_win.show()

    print("\n" + "=" * 50)
    print("  黄花梨之译")
    print("=" * 50)
    print(f"  Hotkey:     {config.get('hotkey', 'ctrl+shift+t')}")
    print(f"  Engine:     {config.get('translation_engine', 'google')}")
    print(f"  Theme:      {config.get('theme', 'dark_professional')}")
    print(f"  OCR:        {'Available' if ocr.is_available() else 'Not installed'}")
    print(f"  Terms:      {len(terminology.get_all_terms())} loaded")
    print(f"  Cache:      {cache.stats()['total_entries']} entries")
    print(f"  Tray:       Running (close window to minimize)")
    print("=" * 50)
    print()

    try:
        sys.exit(app.exec_())
    finally:
        hotkey_mgr.unregister()
        print("Goodbye.")


def _show_main_window(main_win):
    """Show and activate the main window."""
    main_win.show()
    main_win.raise_()
    main_win.activateWindow()


def _tray_floating_translate(clipboard, floating, translator, config, cache, main_win):
    """Trigger a floating translation from the tray menu."""
    text = clipboard.get_selected_text_via_copy()
    if not text:
        text = clipboard.get_text_and_restore()
    if not text:
        return
    engine = config.get("translation_engine", "google")
    try:
        result = translator.translate(text, engine)
        floating.show_translation(
            result["original"], result["translated"],
            result["engine"], result.get("terms_applied"),
        )
        if config.get("cache_enabled", True):
            cache.put(
                result["original"], result["translated"],
                result["engine"],
                config.get("source_lang", "en"),
                config.get("target_lang", "zh"),
            )
        main_win._usage_tracker.record(result["engine"], len(result["original"]))
    except Exception as e:
        floating.show_translation(text, f"Error: {e}", engine)


def _on_tray_activated(reason, main_win, floating, clipboard, translator, config, cache):
    """Handle tray icon activation (click/double-click)."""
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        _show_main_window(main_win)
    elif reason == QSystemTrayIcon.ActivationReason.Trigger:
        # Single click: trigger floating translate
        _tray_floating_translate(clipboard, floating, translator, config, cache, main_win)


def _quit_app(app, main_win, config, hotkey_mgr):
    """Properly quit the application."""
    main_win.close()  # Saves geometry via closeEvent
    hotkey_mgr.unregister()
    app.quit()


if __name__ == "__main__":
    main()
