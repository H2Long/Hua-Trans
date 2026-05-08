"""Main application window — sidebar navigation + stacked pages with fade animation."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QStatusBar, QLabel, QFrame, QApplication,
    QGraphicsOpacityEffect,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QCloseEvent

from core.config import load_config, save_config
from core.terminology import TerminologyDB
from core.translator import TranslationManager
from core.cache import TranslationCache
from core.ocr_handler import OCRHandler
from gui.theme import COLORS, FONTS, MAIN_WINDOW_STYLE, set_active_theme
from gui.sidebar import Sidebar
from gui.pages.translation_page import TranslationPage
from gui.pages.history_page import HistoryPage
from gui.pages.terminology_page import TerminologyPage
from gui.pages.settings_page import SettingsPage


class MainWindow(QMainWindow):
    """Main window with sidebar navigation and stacked content pages.

    Features Apple-inspired design with fade transitions between pages
    and a glass sidebar.
    """

    hotkey_translate = pyqtSignal(str)

    def __init__(self, config: dict, terminology: TerminologyDB,
                 translator: TranslationManager, cache: TranslationCache,
                 ocr: OCRHandler):
        super().__init__()
        self.config = config
        self.terminology = terminology
        self.translator = translator
        self.cache = cache
        self.ocr = ocr

        self._setup_ui()
        self._restore_geometry()

    def _setup_ui(self):
        c = COLORS
        self.setWindowTitle("黄花梨之译")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -- Sidebar --------------------------------------------------
        self._sidebar = Sidebar()
        self._sidebar.setStyleSheet(f"QWidget {{ background: {c.bg_surface}; }}")
        main_layout.addWidget(self._sidebar)

        # -- Decorative separator (glow line) -------------------------
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 transparent, stop:0.3 {c.accent_blue}20,
                stop:0.5 {c.accent_blue}40, stop:0.7 {c.accent_blue}20,
                stop:1 transparent);
        """)
        main_layout.addWidget(sep)

        # -- Stacked pages ------------------------------------------
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {c.bg_base};")

        # Page 0: Translation
        self._translation_page = TranslationPage(
            self.config, self.terminology, self.translator,
            self.cache, self.ocr,
        )
        self._translation_page.status_message.connect(self._update_status)
        self._translation_page.translation_done.connect(self._on_translation_done)
        self._stack.addWidget(self._translation_page)

        # Page 1: History
        self._history_page = HistoryPage(self.cache)
        self._history_page.fill_requested.connect(self._fill_translation)
        self._stack.addWidget(self._history_page)

        # Page 2: Terminology
        self._terminology_page = TerminologyPage(self.terminology)
        self._stack.addWidget(self._terminology_page)

        # Page 3: Settings
        self._settings_page = SettingsPage(self.config, self.translator, self.cache)
        self._settings_page.theme_changed.connect(self._on_theme_changed)
        self._stack.addWidget(self._settings_page)

        main_layout.addWidget(self._stack, 1)

        # -- Status bar -----------------------------------------------
        self._status = QStatusBar()
        self.setStatusBar(self._status)

        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background: {c.bg_surface};
                border-top: 1px solid {c.border_subtle};
            }}
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(16, 6, 16, 6)

        self._page_name_label = QLabel("翻译")
        self._page_name_label.setStyleSheet(f"""
            color: {c.text_secondary};
            font-family: {FONTS.body};
            font-size: {FONTS.size_xs}px;
        """)
        status_layout.addWidget(self._page_name_label)

        status_layout.addStretch()

        self._engine_label = QLabel(f"引擎: {self.config.get('translation_engine', 'google')}")
        self._engine_label.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.mono};
            font-size: {FONTS.size_xs}px;
        """)
        status_layout.addWidget(self._engine_label)

        self._status.addWidget(status_frame, 1)

        self._page_names = ["翻译", "历史", "术语", "设置"]

        # -- Connect sidebar ------------------------------------------
        self._sidebar.currentChanged.connect(self._on_nav_changed)
        self._sidebar.themeToggleRequested.connect(self._on_sidebar_theme_toggle)

        # -- Restore last page ----------------------------------------
        last_page = self.config.get("last_page", 0)
        if 0 <= last_page < self._stack.count():
            self._sidebar.set_current_index(last_page)

    def _on_nav_changed(self, index: int):
        """Switch page with fade animation."""
        if self._stack.currentIndex() == index:
            return
        # Fade out → switch → fade in
        effect = QGraphicsOpacityEffect(self._stack)
        effect.setOpacity(1.0)
        self._stack.setGraphicsEffect(effect)
        self._anim = QPropertyAnimation(effect, b"opacity")
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.3)
        self._anim.setEndValue(1.0)
        self._stack.setCurrentIndex(index)
        self._anim.start()
        name = self._page_names[index] if index < len(self._page_names) else ""
        self._page_name_label.setText(name)

    def _update_status(self, message: str):
        self._engine_label.setText(message)

    def _on_translation_done(self, original: str, translated: str, engine: str):
        """Auto-save to history when translation completes."""
        if self.config.get("cache_enabled", True):
            self.cache.put(
                original, translated, engine,
                self.config.get("source_lang", "en"),
                self.config.get("target_lang", "zh"),
            )
            self._history_page.refresh()

    def _fill_translation(self, text: str):
        """Fill source text into translation page and switch to it."""
        self._translation_page._source_edit.setPlainText(text)
        self._sidebar.set_current_index(0)

    def _on_sidebar_theme_toggle(self):
        """Quick-toggle between dark and light themes."""
        from gui.theme import get_active_theme_name
        current = get_active_theme_name()
        new_theme = "minimal_apple" if current != "minimal_apple" else "deep_purple_blue"
        self.config["theme"] = new_theme
        save_config(self.config)
        self._on_theme_changed(new_theme)

    def _on_theme_changed(self, theme_name: str):
        """Handle theme change from settings."""
        set_active_theme(theme_name)
        from gui.theme import MAIN_WINDOW_STYLE, COLORS as new_c
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        # Reapply styles without losing state
        self._translation_page.reapply_theme()
        self._history_page.reapply_theme()
        self._terminology_page.reapply_theme()
        self._settings_page.reapply_theme()
        # Reapply sidebar & separator styles
        self._sidebar.reapply_theme()
        is_dark = theme_name != "minimal_apple"
        self._sidebar.update_theme_toggle_icon(is_dark)
        c = new_c
        self._sidebar.setStyleSheet(f"QWidget {{ background: {c.bg_surface}; }}")

    def _restore_geometry(self):
        geometry = self.config.get("window_geometry")
        state = self.config.get("window_state")
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))
        if state:
            self.restoreState(bytes.fromhex(state))

    def closeEvent(self, event: QCloseEvent):
        self.config["window_geometry"] = self.saveGeometry().toHex().data().decode()
        self.config["window_state"] = self.saveState().toHex().data().decode()
        self.config["last_page"] = self._sidebar.current_index()
        save_config(self.config)
        # Minimize to tray instead of quitting
        if hasattr(self, '_tray') and self._tray.isVisible():
            self.hide()
            event.ignore()
        else:
            super().closeEvent(event)

    def set_page(self, index: int):
        self._sidebar.set_current_index(index)

    def get_translation_page(self):
        return self._translation_page

    def get_settings_page(self):
        return self._settings_page
