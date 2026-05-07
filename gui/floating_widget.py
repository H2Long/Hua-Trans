"""Floating translation popup — Apple-inspired glass design."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QApplication, QComboBox, QFrame,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QCursor, QMouseEvent

from gui.theme import COLORS, FONTS


class FloatingTranslation(QWidget):
    """Frameless floating translation popup with glass effect.

    Supports two modes:
    - full (default): engine selector, terms, original toggle, history nav
    - mini: just translation text + close button, minimal chrome
    """

    closed = pyqtSignal()

    def __init__(self, config: dict, parent=None, available_engines: list[str] | None = None):
        super().__init__(parent)
        self.config = config
        self._available_engines = available_engines or ["google", "deepl", "llm"]
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.timeout.connect(self.close)
        self._session_history: list[dict] = []
        self._history_index: int = -1
        self._mini_mode = config.get("popup_mini_mode", False)
        self._saved_pos = config.get("popup_position")
        self._setup_ui()

    def _setup_ui(self):
        c = COLORS
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self.config.get("popup_opacity", 0.95))
        self.setFixedWidth(self.config.get("popup_width", 480))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        # Container frame — glass effect
        self._frame = QFrame()
        self._frame.setObjectName("floatingFrame")
        self._frame.setStyleSheet(f"""
            QFrame#floatingFrame {{
                background-color: {c.bg_surface}e8;
                border: 1px solid {c.border_default};
                border-radius: 16px;
            }}
        """)
        frame_layout = QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(16, 12, 16, 12)
        frame_layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        self._engine_combo = QComboBox()
        self._engine_combo.addItems([e.upper() for e in self._available_engines])
        self._engine_combo.setFixedWidth(90)
        self._engine_combo.setStyleSheet(f"""
            QComboBox {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 8px;
                padding: 4px 10px;
                font-family: {FONTS.display};
                font-size: 10px;
                font-weight: 600;
            }}
            QComboBox:hover {{ border-color: {c.accent_blue}; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid {c.text_secondary};
                margin-right: 4px;
            }}
            QComboBox QAbstractItemView {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 8px;
                selection-background-color: {c.bg_active};
            }}
        """)
        header.addWidget(self._engine_combo)

        self._terms_label = QLabel("")
        self._terms_label.setStyleSheet(f"""
            color: {c.accent_green};
            font-family: {FONTS.mono};
            font-size: 10px;
        """)
        header.addWidget(self._terms_label)
        header.addStretch()

        # History navigation
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedSize(26, 26)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.setToolTip("上一条翻译")
        self._prev_btn.setEnabled(False)
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c.text_dim};
                border: none;
                border-radius: 13px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {c.accent_blue}; }}
            QPushButton:disabled {{ color: {c.text_dim}40; }}
        """)
        self._prev_btn.clicked.connect(self._history_prev)
        header.addWidget(self._prev_btn)

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedSize(26, 26)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.setToolTip("下一条翻译")
        self._next_btn.setEnabled(False)
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c.text_dim};
                border: none;
                border-radius: 13px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {c.accent_blue}; }}
            QPushButton:disabled {{ color: {c.text_dim}40; }}
        """)
        self._next_btn.clicked.connect(self._history_next)
        header.addWidget(self._next_btn)

        # Mini/full mode toggle
        self._mini_toggle_btn = QPushButton("⊡")
        self._mini_toggle_btn.setFixedSize(26, 26)
        self._mini_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mini_toggle_btn.setToolTip("切换紧凑/完整模式")
        self._mini_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c.text_dim};
                border: none;
                border-radius: 13px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {c.accent_blue}; }}
        """)
        self._mini_toggle_btn.clicked.connect(self._toggle_mini_mode)
        header.addWidget(self._mini_toggle_btn)

        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(26, 26)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setToolTip("复制译文")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c.text_dim};
                border: none;
                border-radius: 13px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {c.accent_green}; }}
        """)
        copy_btn.clicked.connect(self._copy_result)
        header.addWidget(copy_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c.text_dim};
                border: none;
                border-radius: 13px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {c.accent_red};
                background: {c.accent_red}15;
            }}
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        frame_layout.addLayout(header)

        # Separator — subtle gradient line
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 {c.border_default}, stop:0.7 {c.border_default}, stop:1 transparent);
        """)
        frame_layout.addWidget(sep)

        # Original text (collapsed)
        self._orig_label = QLabel()
        self._orig_label.setWordWrap(True)
        self._orig_label.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.body};
            font-size: 11px;
            font-style: italic;
            padding: 4px 0;
        """)
        self._orig_label.hide()
        frame_layout.addWidget(self._orig_label)

        # Toggle button
        self._toggle_btn = QPushButton("▸ 显示原文")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c.text_dim};
                border: none;
                font-family: {FONTS.display};
                font-size: 10px;
                font-weight: 600;
                text-align: left;
                padding: 2px 0;
            }}
            QPushButton:hover {{ color: {c.accent_blue}; }}
        """)
        self._toggle_btn.clicked.connect(self._toggle_original)
        frame_layout.addWidget(self._toggle_btn)

        # Translation result
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_input};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 10px;
                padding: 10px;
                font-family: {FONTS.body};
                font-size: 14px;
                selection-background-color: {c.accent_blue}40;
            }}
            QTextEdit:focus {{ border-color: {c.border_focus}; }}
        """)
        font = QFont("SF Pro Text", self.config.get("font_size", 16))
        self._result_text.setFont(font)
        self._result_text.setMinimumHeight(50)
        self._result_text.setMaximumHeight(300)
        frame_layout.addWidget(self._result_text)

        # Bottom status
        bottom = QHBoxLayout()
        bottom.setSpacing(6)

        self._status_mini = QLabel("READY")
        self._status_mini.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.mono};
            font-size: 10px;
            letter-spacing: 1px;
        """)
        bottom.addWidget(self._status_mini)
        bottom.addStretch()

        self._timer_label = QLabel("")
        self._timer_label.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.mono};
            font-size: 10px;
        """)
        bottom.addWidget(self._timer_label)
        frame_layout.addLayout(bottom)

        layout.addWidget(self._frame)

    def _toggle_original(self):
        if self._orig_label.isVisible():
            self._orig_label.hide()
            self._toggle_btn.setText("▸ 显示原文")
        else:
            self._orig_label.show()
            self._toggle_btn.setText("▾ 隐藏原文")

    def _copy_result(self):
        """Copy translated text to clipboard."""
        from PyQt5.QtWidgets import QApplication as QtApp
        QtApp.clipboard().setText(self._result_text.toPlainText())

    def show_translation(self, original: str, translated: str,
                         engine: str, terms=None):
        """Show translation result in the popup."""
        c = COLORS

        # Add to session history
        entry = {"original": original, "translated": translated, "engine": engine, "terms": terms}
        # Remove forward history if we're not at the end
        if self._history_index < len(self._session_history) - 1:
            self._session_history = self._session_history[:self._history_index + 1]
        self._session_history.append(entry)
        self._history_index = len(self._session_history) - 1
        self._update_history_buttons()

        self._display_entry(entry)

        # Position: use last saved position, otherwise near mouse
        if self._saved_pos:
            self.move(self._saved_pos["x"], self._saved_pos["y"])
        else:
            self._position_near_mouse()
        self._status_mini.setText(f"VIA {engine.upper()}")

        # Mini mode: hide chrome
        if self._mini_mode:
            self._engine_combo.hide()
            self._terms_label.hide()
            self._toggle_btn.hide()
            self._orig_label.hide()
            self._prev_btn.hide()
            self._next_btn.hide()
            self._status_mini.hide()
            self._timer_label.hide()
            self._result_text.setMaximumHeight(150)
            self._result_text.setMinimumHeight(24)
            self.setFixedWidth(320)
        else:
            self._engine_combo.show()
            self._toggle_btn.show()
            self._prev_btn.show()
            self._next_btn.show()
            self._status_mini.show()
            self._timer_label.show()
            self._result_text.setMaximumHeight(300)
            self._result_text.setMinimumHeight(50)
            self.setFixedWidth(self.config.get("popup_width", 480))

        timeout = self.config.get("auto_hide_seconds", 10)
        if timeout > 0:
            self._auto_hide_timer.start(timeout * 1000)
            self._timer_label.setText(f"{timeout}s 后自动关闭")
        else:
            self._timer_label.setText("")

        self.setWindowOpacity(self.config.get("popup_opacity", 0.95))
        self.show()
        self.raise_()
        self.activateWindow()

    def _display_entry(self, entry: dict):
        """Display a history entry in the widget."""
        c = COLORS
        original = entry["original"]
        translated = entry["translated"]
        engine = entry["engine"]
        terms = entry.get("terms")

        self._orig_label.setText(original[:200] + ("..." if len(original) > 200 else ""))
        self._orig_label.hide()
        self._toggle_btn.setText("▸ 显示原文")
        self._result_text.setPlainText(translated)

        if terms:
            terms_str = " | ".join(f"{en}→{zh}" for en, zh in terms[:5])
            if len(terms) > 5:
                terms_str += f" [+{len(terms) - 5}]"
            self._terms_label.setText(terms_str)
        else:
            self._terms_label.setText("")

        engine_upper = engine.upper()
        idx = self._engine_combo.findText(engine_upper)
        if idx >= 0:
            self._engine_combo.setCurrentIndex(idx)

        doc = self._result_text.document()
        doc.setTextWidth(self._result_text.viewport().width())
        height = min(300, max(50, int(doc.size().height()) + 16))
        self._result_text.setFixedHeight(height)

    def _history_prev(self):
        """Navigate to previous translation in session history."""
        if self._history_index > 0:
            self._history_index -= 1
            self._display_entry(self._session_history[self._history_index])
            self._update_history_buttons()

    def _history_next(self):
        """Navigate to next translation in session history."""
        if self._history_index < len(self._session_history) - 1:
            self._history_index += 1
            self._display_entry(self._session_history[self._history_index])
            self._update_history_buttons()

    def _update_history_buttons(self):
        """Enable/disable history navigation buttons."""
        self._prev_btn.setEnabled(self._history_index > 0)
        self._next_btn.setEnabled(self._history_index < len(self._session_history) - 1)

    def set_mini_mode(self, enabled: bool):
        """Toggle compact mini mode."""
        self._mini_mode = enabled
        self.config["popup_mini_mode"] = enabled

    def _toggle_mini_mode(self):
        """Toggle between mini and full mode, re-displaying current entry."""
        self._mini_mode = not self._mini_mode
        self.config["popup_mini_mode"] = self._mini_mode
        # Re-display current entry with new mode
        if self._session_history and self._history_index >= 0:
            self._display_entry(self._session_history[self._history_index])
            # Apply visibility
            if self._mini_mode:
                self._engine_combo.hide()
                self._terms_label.hide()
                self._toggle_btn.hide()
                self._orig_label.hide()
                self._prev_btn.hide()
                self._next_btn.hide()
                self._status_mini.hide()
                self._timer_label.hide()
                self._result_text.setMaximumHeight(150)
                self._result_text.setMinimumHeight(24)
                self.setFixedWidth(320)
            else:
                self._engine_combo.show()
                self._toggle_btn.show()
                self._prev_btn.show()
                self._next_btn.show()
                self._status_mini.show()
                self._timer_label.show()
                self._result_text.setMaximumHeight(300)
                self._result_text.setMinimumHeight(50)
                self.setFixedWidth(self.config.get("popup_width", 480))

    def _position_near_mouse(self):
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if not screen:
            screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        x = cursor_pos.x() + 16
        y = cursor_pos.y() + 16

        self.adjustSize()
        w, h = self.width(), self.height()
        if x + w > screen_rect.right():
            x = cursor_pos.x() - w - 16
        if y + h > screen_rect.bottom():
            y = cursor_pos.y() - h - 16
        x = max(screen_rect.left(), x)
        y = max(screen_rect.top(), y)

        self.move(x, y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if hasattr(self, '_drag_pos') and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def closeEvent(self, event):
        self._auto_hide_timer.stop()
        # Remember position for next time
        self.config["popup_position"] = {"x": self.x(), "y": self.y()}
        self.closed.emit()
        super().closeEvent(event)
