"""Sidebar navigation widget — glass-morphism design with SVG icons."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QFrame, QStyledItemDelegate, QStyle,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QPainter, QPixmap, QPen, QPalette

from gui.theme import COLORS, FONTS


# -- Inline SVG icons (Lucide-style, 20x20) -------------------------
def _make_icon(path_data: str, color: str, size: int = 20) -> QIcon:
    """Create a QIcon from an SVG path with the given color."""
    from PyQt5.QtSvg import QSvgRenderer
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}"
        viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        {path_data}
    </svg>'''
    renderer = QSvgRenderer(bytearray(svg.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# Lucide icon paths
_ICON_PATHS = {
    "translate": '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>',
    "history": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "book": '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
}


def _get_nav_items() -> list[tuple[str, str, str]]:
    """Return (icon_key, label, tooltip) for each nav item."""
    return [
        ("translate", "翻译", "翻译工作区 (Ctrl+1)"),
        ("history", "历史", "翻译历史 (Ctrl+2)"),
        ("book", "术语", "术语管理 (Ctrl+3)"),
        ("settings", "设置", "应用设置 (Ctrl+4)"),
    ]


class Sidebar(QWidget):
    """Vertical sidebar navigation with glass-morphism effect."""

    currentChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self._current_index = 0
        self._setup_ui()

    def _setup_ui(self):
        c = COLORS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # -- Sidebar background ----------------------------------------
        self.setStyleSheet(f"QWidget {{ background: {c.bg_surface}; }}")

        # -- App title ------------------------------------------------
        title_frame = QFrame()
        title_frame.setFixedHeight(68)
        title_frame.setStyleSheet(f"""
            QFrame {{
                background: {c.bg_surface};
                border-bottom: 1px solid {c.border_subtle};
            }}
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(22, 16, 22, 12)

        title = QLabel("黄花梨之译")
        title.setStyleSheet(f"""
            color: {c.text_bright};
            font-family: {FONTS.display};
            font-size: 19px;
            font-weight: 800;
            letter-spacing: 4px;
        """)
        title_layout.addWidget(title)

        subtitle = QLabel("TranslateTor")
        subtitle.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.mono};
            font-size: 11px;
            letter-spacing: 4px;
        """)
        title_layout.addWidget(subtitle)
        layout.addWidget(title_frame)

        # -- Navigation list ------------------------------------------
        self._list = QListWidget()
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Compute alpha-blended variants of accent color for selection/highlight
        accent_no_hash = c.accent_blue.lstrip("#")
        accent_r, accent_g, accent_b = int(accent_no_hash[0:2], 16), int(accent_no_hash[2:4], 16), int(accent_no_hash[4:6], 16)

        # Force palette to prevent system theme color bleed
        pal = self._list.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(c.bg_surface))
        pal.setColor(QPalette.ColorRole.Window, QColor(c.bg_surface))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(accent_r, accent_g, accent_b, 48))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(c.text_bright))
        self._list.setPalette(pal)

        self._list.setStyleSheet(f"""
            QListWidget {{
                background: {c.bg_surface};
                border: none;
                padding: 14px 0;
                outline: 0;
            }}
            QListWidget::item {{
                background: transparent;
                border: none;
                outline: none;
                padding: 0;
                margin: 5px 14px;
                border-radius: 12px;
                height: 52px;
            }}
            QListWidget::item:selected {{
                background: rgba({accent_r}, {accent_g}, {accent_b}, 0.15);
                border: none;
                outline: none;
            }}
            QListWidget::item:hover {{
                background: {c.bg_hover};
                border: none;
                outline: none;
            }}
        """)

        nav_items = _get_nav_items()
        for icon_key, label, tooltip in nav_items:
            item = QListWidgetItem()
            item.setSizeHint(QSize(192, 48))
            item.setToolTip(tooltip)
            item.setData(Qt.ItemDataRole.UserRole, icon_key)
            self._list.addItem(item)

        self._list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self._list, 1)

        # -- Decorative separator line --------------------------------
        glow_line = QFrame()
        glow_line.setFixedHeight(1)
        glow_line.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.5 {c.accent_blue}40, stop:1 transparent);
                margin: 0 20px;
            }}
        """)
        layout.addWidget(glow_line)

        # -- Version footer -------------------------------------------
        footer = QFrame()
        footer.setFixedHeight(52)
        footer.setStyleSheet(f"""
            QFrame {{
                background: {c.bg_surface};
                border-top: 1px solid {c.border_subtle};
            }}
        """)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(22, 8, 22, 8)
        footer_layout.setSpacing(4)

        # Hotkey status row
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_row.setContentsMargins(0, 0, 0, 0)

        self._hotkey_dot = QLabel("●")
        self._hotkey_dot.setFixedWidth(14)
        self._hotkey_dot.setStyleSheet(f"""
            color: {c.accent_green};
            font-size: 8px;
            padding: 0;
        """)
        status_row.addWidget(self._hotkey_dot)

        self._hotkey_status = QLabel("热键已启用")
        self._hotkey_status.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.mono};
            font-size: 10px;
            letter-spacing: 0.5px;
        """)
        status_row.addWidget(self._hotkey_status)
        status_row.addStretch()
        footer_layout.addLayout(status_row)

        version = QLabel("v1.0")
        version.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.mono};
            font-size: 10px;
            letter-spacing: 1px;
        """)
        footer_layout.addWidget(version)
        layout.addWidget(footer)

        # -- Custom item painting -------------------------------------
        self._list.setItemDelegate(_SidebarDelegate(self._list))

        # Select first item
        self._list.setCurrentRow(0)

    def _on_row_changed(self, row: int):
        if row != self._current_index:
            self._current_index = row
            self.currentChanged.emit(row)

    def set_current_index(self, index: int):
        """Programmatically set the selected item."""
        self._list.setCurrentRow(index)

    def current_index(self) -> int:
        return self._current_index

    def set_hotkey_status(self, ok: bool):
        """Update the hotkey status indicator dot."""
        c = COLORS
        if ok:
            self._hotkey_dot.setStyleSheet(f"color: {c.accent_green}; font-size: 8px; padding: 0;")
            self._hotkey_status.setText("热键已启用")
        else:
            self._hotkey_dot.setStyleSheet(f"color: {c.accent_red}; font-size: 8px; padding: 0;")
            self._hotkey_status.setText("热键未注册")

    def reapply_theme(self):
        """Reapply styles after theme switch without losing state."""
        c = COLORS
        self.setStyleSheet(f"QWidget {{ background: {c.bg_surface}; }}")
        # Recompute accent alpha values for palette
        accent_no_hash = c.accent_blue.lstrip("#")
        accent_r = int(accent_no_hash[0:2], 16)
        accent_g = int(accent_no_hash[2:4], 16)
        accent_b = int(accent_no_hash[4:6], 16)
        pal = self._list.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(c.bg_surface))
        pal.setColor(QPalette.ColorRole.Window, QColor(c.bg_surface))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(accent_r, accent_g, accent_b, 48))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(c.text_bright))
        self._list.setPalette(pal)
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: {c.bg_surface};
                border: none;
                padding: 14px 0;
                outline: 0;
            }}
            QListWidget::item {{
                background: transparent;
                border: none;
                outline: none;
                padding: 0;
                margin: 5px 14px;
                border-radius: 12px;
                height: 52px;
            }}
            QListWidget::item:selected {{
                background: rgba({accent_r}, {accent_g}, {accent_b}, 0.15);
                border: none;
                outline: none;
            }}
            QListWidget::item:hover {{
                background: {c.bg_hover};
                border: none;
                outline: none;
            }}
        """)
        # Refresh delegate (it reads COLORS at paint time, so just trigger repaint)
        self._list.update()


class _SidebarDelegate(QStyledItemDelegate):
    """Simplified delegate: icon + label + solid accent bar.

    Background styling handled by QSS. Delegate only paints:
    - Solid accent bar for selected items
    - SVG icon with color transitions
    - Text label
    """

    def paint(self, painter, option, index):
        """Paint icon + label only. Background handled by QSS."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = COLORS
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hover = bool(option.state & QStyle.StateFlag.State_MouseOver)

        rect = option.rect

        # Left accent bar for selected (with subtle glow)
        if is_selected:
            bar = rect.adjusted(0, 10, 0, -10)
            bar.setWidth(4)
            painter.fillRect(bar, QColor(c.accent_blue))

        # Icon
        icon_key = index.data(Qt.ItemDataRole.UserRole)
        if is_selected:
            icon_color = c.accent_blue
        elif is_hover:
            icon_color = c.text_bright
        else:
            icon_color = c.text_secondary

        if icon_key in _ICON_PATHS:
            icon = _make_icon(_ICON_PATHS[icon_key], icon_color)
            icon_rect = rect.adjusted(20, 0, 0, 0)
            icon_rect.setWidth(20)
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignVCenter)

        # Label
        label_map = {item[0]: item[1] for item in _get_nav_items()}
        label_text = label_map.get(icon_key, "")
        if is_selected:
            text_color = QColor(c.accent_blue)
        elif is_hover:
            text_color = QColor(c.text_bright)
        else:
            text_color = QColor(c.text_primary)

        font = QFont()
        font.setFamily(FONTS.display.split(",")[0].strip("' "))
        font.setPixelSize(FONTS.size_sm)
        font.setWeight(QFont.Weight.DemiBold if is_selected else QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QPen(text_color))

        text_rect = rect.adjusted(50, 0, -14, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, label_text)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(192, 48)
