"""Reusable search bar with debounced text input."""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from gui.theme import COLORS, FONTS


class SearchBar(QWidget):
    """Search input with clear button and 300ms debounce."""

    textChanged = pyqtSignal(str)

    def __init__(self, placeholder: str = "搜索...", parent=None):
        super().__init__(parent)
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(self._emit_text)
        self._setup_ui(placeholder)

    def _setup_ui(self, placeholder: str):
        c = COLORS
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {c.bg_input};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 10px;
                padding: 9px 14px;
                font-family: {FONTS.body};
                font-size: {FONTS.size_sm}px;
            }}
            QLineEdit:focus {{
                border-color: {c.border_focus};
            }}
        """)
        self._input.textChanged.connect(lambda: self._debounce.start())
        layout.addWidget(self._input)

        self._clear_btn = QPushButton("✕")
        self._clear_btn.setFixedSize(30, 30)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {c.text_dim};
                border: none;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {c.accent_red};
                background: {c.accent_red}15;
            }}
        """)
        self._clear_btn.clicked.connect(self.clear)
        self._clear_btn.hide()
        layout.addWidget(self._clear_btn)

        self._input.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        self._clear_btn.setVisible(bool(text))

    def _emit_text(self):
        self.textChanged.emit(self._input.text())

    def clear(self):
        self._input.clear()

    def text(self) -> str:
        return self._input.text()
