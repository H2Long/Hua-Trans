"""Stylesheet generator — builds Qt stylesheets from theme data.

All widget styles are generated here. Import via theme.py facade.
Apple-inspired design: large radii, generous spacing, subtle depth.
"""

from .colors import ThemeColors, ThemeFonts


def generate_main_window_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QMainWindow {{
    background-color: {c.bg_base};
}}

QMainWindow::separator {{
    background: {c.border_subtle};
    width: 1px;
    height: 1px;
}}

QToolBar {{
    background: {c.bg_surface};
    border-bottom: 1px solid {c.border_default};
    padding: 8px 16px;
    spacing: 10px;
}}

QToolBar::separator {{
    width: 1px;
    background: {c.border_default};
    margin: 4px 8px;
}}

QToolButton {{
    background: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    padding: 8px 16px;
    font-family: {f.display};
    font-size: {f.size_sm}px;
    font-weight: 600;
}}

QToolButton:hover {{
    background: {c.bg_hover};
    border-color: {c.accent_blue};
    color: {c.text_bright};
}}

QToolButton:pressed {{
    background: {c.bg_active};
    color: {c.text_bright};
}}

QLabel {{
    color: {c.text_secondary};
    font-family: {f.body};
    font-size: {f.size_sm}px;
}}

QStatusBar {{
    background: {c.bg_surface};
    border-top: 1px solid {c.border_default};
    color: {c.text_secondary};
    font-family: {f.mono};
    font-size: {f.size_xs}px;
    padding: 6px 16px;
}}

QStatusBar::item {{
    border: none;
}}
"""


def generate_text_edit_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QTextEdit {{
    background: {c.bg_input};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 14px;
    padding: 14px;
    font-family: {f.body};
    font-size: {f.size_md}px;
    selection-background-color: {c.accent_blue}40;
    selection-color: {c.text_bright};
}}

QTextEdit:focus {{
    border-color: {c.border_focus};
}}

QTextEdit QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    border: none;
    margin: 2px;
}}

QTextEdit QScrollBar::handle:vertical {{
    background: {c.scroll_thumb};
    border-radius: 4px;
    min-height: 30px;
}}

QTextEdit QScrollBar::handle:vertical:hover {{
    background: {c.scroll_hover};
}}

QTextEdit QScrollBar::add-line:vertical,
QTextEdit QScrollBar::sub-line:vertical,
QTextEdit QScrollBar::add-page:vertical,
QTextEdit QScrollBar::sub-page:vertical {{
    height: 0;
    background: none;
}}
"""


def generate_list_widget_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QListWidget {{
    background: {c.bg_input};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 14px;
    padding: 6px;
    font-family: {f.body};
    font-size: {f.size_sm}px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px 12px;
    border-radius: 10px;
    margin: 2px 0;
    border-left: 3px solid transparent;
}}

QListWidget::item:hover {{
    background: {c.bg_hover};
    color: {c.text_bright};
    border-left-color: {c.accent_blue};
}}

QListWidget::item:selected {{
    background: {c.bg_active};
    color: {c.text_bright};
    border-left-color: {c.accent_blue};
}}

QListWidget QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    border: none;
}}

QListWidget QScrollBar::handle:vertical {{
    background: {c.scroll_thumb};
    border-radius: 4px;
}}

QListWidget QScrollBar::handle:vertical:hover {{
    background: {c.scroll_hover};
}}

QListWidget QScrollBar::add-line:vertical,
QListWidget QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


def generate_combo_box_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QComboBox {{
    background: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    padding: 8px 14px;
    font-family: {f.display};
    font-size: {f.size_sm}px;
    min-width: 100px;
}}

QComboBox:hover {{
    border-color: {c.accent_blue};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c.text_secondary};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    selection-background-color: {c.bg_active};
    selection-color: {c.text_bright};
    padding: 6px;
    outline: none;
}}
"""


def generate_push_button_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QPushButton {{
    background: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    padding: 10px 24px;
    font-family: {f.display};
    font-size: {f.size_sm}px;
    font-weight: 600;
}}

QPushButton:hover {{
    background: {c.bg_hover};
    border-color: {c.accent_blue};
    color: {c.text_bright};
}}

QPushButton:pressed {{
    background: {c.bg_active};
    color: {c.text_bright};
}}

QPushButton:disabled {{
    background: {c.bg_surface};
    color: {c.text_dim};
    border-color: {c.border_subtle};
}}

QPushButton#primaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {c.accent_blue}, stop:1 {c.accent_blue_hover});
    border-color: transparent;
    color: #ffffff;
    font-size: {f.size_md}px;
    padding: 12px 28px;
}}

QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {c.accent_blue_hover}, stop:1 {c.accent_blue});
    border-color: transparent;
}}

QPushButton#primaryButton:pressed {{
    background: {c.accent_blue};
}}

QPushButton#successButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c.accent_green}, stop:1 {c.accent_green_hover});
    border-color: transparent;
    color: #ffffff;
    font-size: {f.size_md}px;
    padding: 12px 28px;
}}

QPushButton#successButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c.accent_green_hover}, stop:1 {c.accent_green});
    border-color: transparent;
}}

QPushButton#successButton:pressed {{
    background: {c.accent_green};
}}

QPushButton#dangerButton {{
    background: transparent;
    border-color: {c.accent_red};
    color: {c.accent_red};
}}

QPushButton#dangerButton:hover {{
    background: {c.accent_red};
    color: #ffffff;
}}
"""


def generate_tab_widget_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QTabWidget::pane {{
    background: {c.bg_surface};
    border: 1px solid {c.border_default};
    border-top: none;
    border-radius: 0 0 14px 14px;
}}

QTabBar::tab {{
    background: {c.bg_elevated};
    color: {c.text_secondary};
    border: 1px solid {c.border_default};
    border-bottom: none;
    padding: 10px 24px;
    font-family: {f.display};
    font-size: {f.size_sm}px;
    font-weight: 600;
    margin-right: 2px;
    border-radius: 10px 10px 0 0;
}}

QTabBar::tab:hover {{
    background: {c.bg_hover};
    color: {c.text_bright};
}}

QTabBar::tab:selected {{
    background: {c.bg_surface};
    color: {c.accent_blue};
    border-bottom: 3px solid {c.accent_blue};
}}
"""


def generate_spin_box_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QSpinBox {{
    background: {c.bg_input};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    padding: 8px 12px;
    font-family: {f.mono};
    font-size: {f.size_md}px;
}}

QSpinBox:focus {{
    border-color: {c.border_focus};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background: {c.bg_elevated};
    border: none;
    width: 22px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {c.bg_hover};
}}
"""


def generate_splitter_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QSplitter {{
    background: {c.bg_base};
}}

QSplitter::handle {{
    background: {c.border_default};
    width: 1px;
    height: 1px;
}}

QSplitter::handle:hover {{
    background: {c.accent_blue};
}}
"""


def generate_progress_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QProgressDialog {{
    background: {c.bg_surface};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 14px;
}}

QProgressBar {{
    background: {c.bg_input};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    text-align: center;
    color: {c.text_primary};
    font-family: {f.mono};
    font-weight: 600;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c.accent_blue}, stop:1 {c.accent_blue_hover});
    border-radius: 9px;
}}
"""


def generate_message_box_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QMessageBox {{
    background: {c.bg_surface};
}}

QMessageBox QLabel {{
    color: {c.text_primary};
    font-family: {f.body};
    font-size: {f.size_md}px;
}}

QMessageBox QPushButton {{
    background: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    padding: 8px 24px;
    font-family: {f.display};
    font-weight: 600;
    min-width: 80px;
}}

QMessageBox QPushButton:hover {{
    border-color: {c.accent_blue};
    color: {c.text_bright};
}}
"""


def generate_floating_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QFrame#floatingFrame {{
    background-color: {c.bg_surface};
    border: 1px solid {c.border_default};
    border-radius: 16px;
}}

QLabel {{
    color: {c.text_secondary};
    font-family: {f.body};
    font-size: {f.size_sm}px;
}}

QTextEdit {{
    background: {c.bg_input};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    padding: 10px;
    font-family: {f.body};
    font-size: {f.size_lg}px;
}}

QComboBox {{
    background: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 8px;
    padding: 5px 10px;
    font-family: {f.display};
    font-size: {f.size_xs}px;
    font-weight: 600;
}}

QPushButton {{
    background: transparent;
    color: {c.text_secondary};
    border: none;
    font-size: {f.size_md}px;
}}

QPushButton:hover {{
    color: {c.accent_red};
}}
"""


def generate_line_edit_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QLineEdit {{
    background: {c.bg_input};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 10px;
    padding: 10px 14px;
    font-family: {f.body};
    font-size: {f.size_md}px;
    selection-background-color: {c.accent_blue}40;
}}

QLineEdit:focus {{
    border-color: {c.border_focus};
}}
"""


def generate_table_widget_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QTableWidget {{
    background: {c.bg_input};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 14px;
    gridline-color: {c.border_subtle};
    font-family: {f.body};
    font-size: {f.size_sm}px;
    selection-background-color: {c.bg_active};
    selection-color: {c.text_bright};
    outline: none;
}}

QTableWidget::item {{
    padding: 8px 12px;
    border: none;
}}

QTableWidget::item:hover {{
    background: {c.bg_hover};
}}

QHeaderView::section {{
    background: {c.bg_surface};
    color: {c.text_secondary};
    border: none;
    border-bottom: 1px solid {c.border_default};
    border-right: 1px solid {c.border_subtle};
    padding: 10px 12px;
    font-family: {f.display};
    font-size: {f.size_sm}px;
    font-weight: 600;
}}

QHeaderView::section:hover {{
    background: {c.bg_hover};
    color: {c.text_bright};
}}

QTableWidget QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    border: none;
}}

QTableWidget QScrollBar::handle:vertical {{
    background: {c.scroll_thumb};
    border-radius: 4px;
}}

QTableWidget QScrollBar::handle:vertical:hover {{
    background: {c.scroll_hover};
}}

QTableWidget QScrollBar::add-line:vertical,
QTableWidget QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


def generate_group_box_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QGroupBox {{
    background: {c.bg_elevated};
    border: 1px solid {c.border_default};
    border-radius: 12px;
    margin-top: 14px;
    padding: 20px 16px 16px 16px;
    font-family: {f.display};
    font-size: {f.size_sm}px;
    font-weight: 600;
    color: {c.text_secondary};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    color: {c.accent_blue};
}}
"""


def generate_slider_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QSlider::groove:horizontal {{
    background: {c.border_default};
    height: 5px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {c.accent_blue};
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
}}

QSlider::handle:horizontal:hover {{
    background: {c.accent_blue_hover};
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c.accent_blue}, stop:1 {c.accent_blue_hover});
    border-radius: 2px;
}}
"""


def generate_check_box_style(c: ThemeColors, f: ThemeFonts) -> str:
    return f"""
QCheckBox {{
    color: {c.text_primary};
    font-family: {f.body};
    font-size: {f.size_md}px;
    spacing: 10px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {c.border_default};
    border-radius: 5px;
    background: {c.bg_input};
}}

QCheckBox::indicator:hover {{
    border-color: {c.accent_blue};
}}

QCheckBox::indicator:checked {{
    background: {c.accent_blue};
    border-color: {c.accent_blue};
}}
"""


def generate_all_styles(theme_name: str) -> dict:
    """Generate all named stylesheets for the given theme."""
    from .colors import get_theme
    c, f = get_theme(theme_name)
    return {
        "COLORS": c,
        "FONTS": f,
        "MAIN_WINDOW_STYLE": generate_main_window_style(c, f),
        "TEXT_EDIT_STYLE": generate_text_edit_style(c, f),
        "LIST_WIDGET_STYLE": generate_list_widget_style(c, f),
        "COMBO_BOX_STYLE": generate_combo_box_style(c, f),
        "PUSH_BUTTON_STYLE": generate_push_button_style(c, f),
        "TAB_WIDGET_STYLE": generate_tab_widget_style(c, f),
        "SPIN_BOX_STYLE": generate_spin_box_style(c, f),
        "SPLITTER_STYLE": generate_splitter_style(c, f),
        "PROGRESS_STYLE": generate_progress_style(c, f),
        "MESSAGE_BOX_STYLE": generate_message_box_style(c, f),
        "FLOATING_STYLE": generate_floating_style(c, f),
        "LINE_EDIT_STYLE": generate_line_edit_style(c, f),
        "TABLE_WIDGET_STYLE": generate_table_widget_style(c, f),
        "GROUP_BOX_STYLE": generate_group_box_style(c, f),
        "SLIDER_STYLE": generate_slider_style(c, f),
        "CHECK_BOX_STYLE": generate_check_box_style(c, f),
    }
