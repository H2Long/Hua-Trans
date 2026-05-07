"""Theme facade — exports active theme constants for all widgets.

Maintains backward-compatible export names (COLORS, FONTS, *_STYLE)
while delegating to the colors/styles modules.

IMPORTANT: Always access via `gui.theme.COLORS` (module attribute),
not `from gui.theme import COLORS` (local binding won't update on theme switch).
"""

from .colors import (
    ThemeColors, ThemeFonts,
    DEEP_PURPLE_BLUE, MINIMAL_APPLE,
    DARK_PROFESSIONAL, MINIMAL_WHITE,
    APPLE_FONTS,
)
from .styles import generate_all_styles

# -- Active theme state ----------------------------------------------
_active_theme_name: str = "deep_purple_blue"
_styles: dict = generate_all_styles(_active_theme_name)

# -- Backward-compatible exports (module-level) ----------------------
COLORS: ThemeColors = _styles["COLORS"]
FONTS: ThemeFonts = _styles["FONTS"]
MAIN_WINDOW_STYLE: str = _styles["MAIN_WINDOW_STYLE"]
TEXT_EDIT_STYLE: str = _styles["TEXT_EDIT_STYLE"]
LIST_WIDGET_STYLE: str = _styles["LIST_WIDGET_STYLE"]
COMBO_BOX_STYLE: str = _styles["COMBO_BOX_STYLE"]
PUSH_BUTTON_STYLE: str = _styles["PUSH_BUTTON_STYLE"]
TAB_WIDGET_STYLE: str = _styles["TAB_WIDGET_STYLE"]
SPIN_BOX_STYLE: str = _styles["SPIN_BOX_STYLE"]
SPLITTER_STYLE: str = _styles["SPLITTER_STYLE"]
PROGRESS_STYLE: str = _styles["PROGRESS_STYLE"]
MESSAGE_BOX_STYLE: str = _styles["MESSAGE_BOX_STYLE"]
FLOATING_STYLE: str = _styles["FLOATING_STYLE"]
LINE_EDIT_STYLE: str = _styles["LINE_EDIT_STYLE"]
TABLE_WIDGET_STYLE: str = _styles["TABLE_WIDGET_STYLE"]
GROUP_BOX_STYLE: str = _styles["GROUP_BOX_STYLE"]
SLIDER_STYLE: str = _styles["SLIDER_STYLE"]
CHECK_BOX_STYLE: str = _styles["CHECK_BOX_STYLE"]


def set_active_theme(name: str):
    """Switch the active theme and regenerate all exports."""
    global _active_theme_name, _styles
    global COLORS, FONTS, MAIN_WINDOW_STYLE, TEXT_EDIT_STYLE
    global LIST_WIDGET_STYLE, COMBO_BOX_STYLE, PUSH_BUTTON_STYLE
    global TAB_WIDGET_STYLE, SPIN_BOX_STYLE, SPLITTER_STYLE
    global PROGRESS_STYLE, MESSAGE_BOX_STYLE, FLOATING_STYLE
    global LINE_EDIT_STYLE, TABLE_WIDGET_STYLE, GROUP_BOX_STYLE
    global SLIDER_STYLE, CHECK_BOX_STYLE

    _active_theme_name = name
    _styles = generate_all_styles(name)

    COLORS = _styles["COLORS"]
    FONTS = _styles["FONTS"]
    MAIN_WINDOW_STYLE = _styles["MAIN_WINDOW_STYLE"]
    TEXT_EDIT_STYLE = _styles["TEXT_EDIT_STYLE"]
    LIST_WIDGET_STYLE = _styles["LIST_WIDGET_STYLE"]
    COMBO_BOX_STYLE = _styles["COMBO_BOX_STYLE"]
    PUSH_BUTTON_STYLE = _styles["PUSH_BUTTON_STYLE"]
    TAB_WIDGET_STYLE = _styles["TAB_WIDGET_STYLE"]
    SPIN_BOX_STYLE = _styles["SPIN_BOX_STYLE"]
    SPLITTER_STYLE = _styles["SPLITTER_STYLE"]
    PROGRESS_STYLE = _styles["PROGRESS_STYLE"]
    MESSAGE_BOX_STYLE = _styles["MESSAGE_BOX_STYLE"]
    FLOATING_STYLE = _styles["FLOATING_STYLE"]
    LINE_EDIT_STYLE = _styles["LINE_EDIT_STYLE"]
    TABLE_WIDGET_STYLE = _styles["TABLE_WIDGET_STYLE"]
    GROUP_BOX_STYLE = _styles["GROUP_BOX_STYLE"]
    SLIDER_STYLE = _styles["SLIDER_STYLE"]
    CHECK_BOX_STYLE = _styles["CHECK_BOX_STYLE"]


def set_accent_color(hex_color: str):
    """Override accent_blue and accent_blue_hover for the active theme."""
    from .colors import THEMES
    c = COLORS
    # Build a new ThemeColors with the custom accent
    updated = ThemeColors(
        bg_base=c.bg_base, bg_surface=c.bg_surface,
        bg_elevated=c.bg_elevated, bg_hover=c.bg_hover,
        bg_active=c.bg_active, bg_input=c.bg_input,
        text_primary=c.text_primary, text_secondary=c.text_secondary,
        text_dim=c.text_dim, text_bright=c.text_bright,
        accent_blue=hex_color,
        accent_blue_hover=_lighten(hex_color, 20),
        accent_green=c.accent_green, accent_green_hover=c.accent_green_hover,
        accent_orange=c.accent_orange,
        accent_red=c.accent_red,
        border_default=c.border_default, border_focus=hex_color,
        border_subtle=c.border_subtle,
        scroll_thumb=c.scroll_thumb, scroll_hover=c.scroll_hover,
        shadow_color=c.shadow_color,
    )
    # Store updated colors in the current styles
    _styles["COLORS"] = updated
    _regenerate_from_colors(updated)


def _lighten(hex_color: str, percent: int) -> str:
    """Lighten a hex color by the given percentage."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = min(255, r + int((255 - r) * percent / 100))
    g = min(255, g + int((255 - g) * percent / 100))
    b = min(255, b + int((255 - b) * percent / 100))
    return f"#{r:02x}{g:02x}{b:02x}"


def _regenerate_from_colors(c: ThemeColors):
    """Regenerate all stylesheet exports from modified colors."""
    from .styles import (
        generate_main_window_style, generate_text_edit_style,
        generate_list_widget_style, generate_combo_box_style,
        generate_push_button_style, generate_tab_widget_style,
        generate_spin_box_style, generate_splitter_style,
        generate_progress_style, generate_message_box_style,
        generate_floating_style, generate_line_edit_style,
        generate_table_widget_style, generate_group_box_style,
        generate_slider_style, generate_check_box_style,
    )
    global COLORS, FONTS, MAIN_WINDOW_STYLE, TEXT_EDIT_STYLE
    global LIST_WIDGET_STYLE, COMBO_BOX_STYLE, PUSH_BUTTON_STYLE
    global TAB_WIDGET_STYLE, SPIN_BOX_STYLE, SPLITTER_STYLE
    global PROGRESS_STYLE, MESSAGE_BOX_STYLE, FLOATING_STYLE
    global LINE_EDIT_STYLE, TABLE_WIDGET_STYLE, GROUP_BOX_STYLE
    global SLIDER_STYLE, CHECK_BOX_STYLE

    f = FONTS
    COLORS = c
    MAIN_WINDOW_STYLE = generate_main_window_style(c, f)
    TEXT_EDIT_STYLE = generate_text_edit_style(c, f)
    LIST_WIDGET_STYLE = generate_list_widget_style(c, f)
    COMBO_BOX_STYLE = generate_combo_box_style(c, f)
    PUSH_BUTTON_STYLE = generate_push_button_style(c, f)
    TAB_WIDGET_STYLE = generate_tab_widget_style(c, f)
    SPIN_BOX_STYLE = generate_spin_box_style(c, f)
    SPLITTER_STYLE = generate_splitter_style(c, f)
    PROGRESS_STYLE = generate_progress_style(c, f)
    MESSAGE_BOX_STYLE = generate_message_box_style(c, f)
    FLOATING_STYLE = generate_floating_style(c, f)
    LINE_EDIT_STYLE = generate_line_edit_style(c, f)
    TABLE_WIDGET_STYLE = generate_table_widget_style(c, f)
    GROUP_BOX_STYLE = generate_group_box_style(c, f)
    SLIDER_STYLE = generate_slider_style(c, f)
    CHECK_BOX_STYLE = generate_check_box_style(c, f)


def get_active_theme_name() -> str:
    """Return the current theme name."""
    return _active_theme_name


def get_active_colors() -> ThemeColors:
    """Return the current theme colors."""
    return COLORS


def get_active_fonts() -> ThemeFonts:
    """Return the current theme fonts."""
    return FONTS


# -- Glitch text helpers (kept for compatibility) ---------------------
GLITCH_TITLE_HTML = """
<span style="
    font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
    font-size: 28px;
    font-weight: bold;
    letter-spacing: 6px;
    color: #7C6CFA;
    text-shadow: 0 0 20px #7C6CFA30;
">黄花梨之译</span>
"""

NEON_TEXT_HTML_TEMPLATE = """
<span style="
    font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
    font-size: {size}px;
    font-weight: bold;
    letter-spacing: {spacing}px;
    color: {color};
">{text}</span>
"""
