"""Theme data layer — color roles and font definitions.

Four themes:
  - Deep Purple Blue (dark, Apple-inspired)
  - Minimal Apple (light, Apple-inspired)
  - Dark Professional (legacy VS Code dark+)
  - Minimal White (legacy light)
All widgets pull colors from here via the styles module.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeColors:
    """Named color roles for a complete UI theme."""
    # Backgrounds (darkest -> lightest)
    bg_base: str        # main window background
    bg_surface: str     # sidebar, panels
    bg_elevated: str    # cards, input fields
    bg_hover: str       # hover states
    bg_active: str      # selected / active item
    bg_input: str       # text input fields

    # Text (brightest -> dimmest)
    text_primary: str   # body text
    text_secondary: str # labels, secondary info
    text_dim: str       # disabled, hints
    text_bright: str    # emphasized text

    # Accent colors
    accent_blue: str    # primary action, links, focus
    accent_blue_hover: str
    accent_green: str   # success, terminology highlights
    accent_green_hover: str
    accent_orange: str  # warning
    accent_red: str     # error, destructive

    # Borders & separators
    border_default: str
    border_focus: str
    border_subtle: str  # very faint separator

    # Scrollbar
    scroll_thumb: str
    scroll_hover: str

    # Shadows
    shadow_color: str


@dataclass(frozen=True)
class ThemeFonts:
    """Font families and sizes."""
    display: str    # headings, sidebar labels
    body: str       # body text, content
    mono: str       # code, technical text

    size_xs: int = 12
    size_sm: int = 14
    size_md: int = 15
    size_lg: int = 16
    size_xl: int = 20
    size_xxl: int = 26


# -- Deep Purple Blue (Apple-inspired dark) --------------------------
DEEP_PURPLE_BLUE = ThemeColors(
    bg_base="#16142a",
    bg_surface="#1d1b35",
    bg_elevated="#252340",
    bg_hover="#2e2c4a",
    bg_active="#3a3760",
    bg_input="#1e1c36",
    text_primary="#e0dff0",
    text_secondary="#9896b0",
    text_dim="#6a688a",
    text_bright="#f0efff",
    accent_blue="#7C6CFA",
    accent_blue_hover="#9588FF",
    accent_green="#5fd4b8",
    accent_green_hover="#7ae8cc",
    accent_orange="#e0a87e",
    accent_red="#ef6b6b",
    border_default="#2a2845",
    border_focus="#7C6CFA",
    border_subtle="#22203a",
    scroll_thumb="#35335880",
    scroll_hover="#45437080",
    shadow_color="#00000040",
)

# -- Minimal Apple (Apple-inspired light) ----------------------------
MINIMAL_APPLE = ThemeColors(
    bg_base="#f5f5f7",
    bg_surface="#ffffff",
    bg_elevated="#ffffff",
    bg_hover="#f0f0f2",
    bg_active="#ececf0",
    bg_input="#ffffff",
    text_primary="#1d1d1f",
    text_secondary="#86868b",
    text_dim="#aeaeb2",
    text_bright="#000000",
    accent_blue="#6e5ce7",
    accent_blue_hover="#7C6CFA",
    accent_green="#34c759",
    accent_green_hover="#52dba3",
    accent_orange="#ff9f0a",
    accent_red="#ff3b30",
    border_default="#d2d2d7",
    border_focus="#6e5ce7",
    border_subtle="#e8e8ed",
    scroll_thumb="#c7c7cc80",
    scroll_hover="#aeaeb280",
    shadow_color="#00000008",
)

# -- Dark Professional (legacy VS Code dark+) ------------------------
DARK_PROFESSIONAL = ThemeColors(
    bg_base="#1e1e1e",
    bg_surface="#252526",
    bg_elevated="#2d2d2d",
    bg_hover="#37373d",
    bg_active="#094771",
    bg_input="#3c3c3c",
    text_primary="#cccccc",
    text_secondary="#969696",
    text_dim="#6a6a6a",
    text_bright="#e0e0e0",
    accent_blue="#0078d4",
    accent_blue_hover="#1a8cff",
    accent_green="#4ec9b0",
    accent_green_hover="#6ee0c6",
    accent_orange="#ce9178",
    accent_red="#f44747",
    border_default="#3c3c3c",
    border_focus="#007acc",
    border_subtle="#2d2d2d",
    scroll_thumb="#424242",
    scroll_hover="#4f4f4f",
    shadow_color="#00000060",
)

# -- Minimal White (legacy light) ------------------------------------
MINIMAL_WHITE = ThemeColors(
    bg_base="#ffffff",
    bg_surface="#f8f9fa",
    bg_elevated="#ffffff",
    bg_hover="#f3f4f6",
    bg_active="#eff6ff",
    bg_input="#ffffff",
    text_primary="#1a1a1a",
    text_secondary="#6b7280",
    text_dim="#9ca3af",
    text_bright="#111827",
    accent_blue="#2563eb",
    accent_blue_hover="#3b82f6",
    accent_green="#059669",
    accent_green_hover="#27b980",
    accent_orange="#d97706",
    accent_red="#dc2626",
    border_default="#e5e7eb",
    border_focus="#3b82f6",
    border_subtle="#f3f4f6",
    scroll_thumb="#d1d5db",
    scroll_hover="#9ca3af",
    shadow_color="#00000010",
)


# -- Font definitions ------------------------------------------------
APPLE_FONTS = ThemeFonts(
    display="'SF Pro Display', 'Segoe UI', 'Noto Sans SC', 'Microsoft YaHei', sans-serif",
    body="'SF Pro Text', 'Segoe UI', 'Noto Sans SC', 'Microsoft YaHei', sans-serif",
    mono="'JetBrains Mono', 'Fira Code', monospace",
)

DARK_FONTS = ThemeFonts(
    display="'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
    body="'JetBrains Mono', 'Cascadia Code', monospace",
    mono="'JetBrains Mono', 'Fira Code', monospace",
)

LIGHT_FONTS = ThemeFonts(
    display="'JetBrains Mono', 'Cascadia Code', 'SF Pro Display', 'Segoe UI', sans-serif",
    body="'JetBrains Mono', 'Cascadia Code', 'SF Pro Text', 'Segoe UI', sans-serif",
    mono="'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
)


# -- Amber Gold (warm dark, comfortable for extended reading) ---------
AMBER_GOLD = ThemeColors(
    bg_base="#1a1814",
    bg_surface="#211f1a",
    bg_elevated="#2a2720",
    bg_hover="#333028",
    bg_active="#3d3a30",
    bg_input="#1e1c17",
    text_primary="#e8e4d8",
    text_secondary="#a09880",
    text_dim="#6b6555",
    text_bright="#f5f0e0",
    accent_blue="#d4a853",
    accent_blue_hover="#e0be6a",
    accent_green="#8ab87a",
    accent_green_hover="#9ec98a",
    accent_orange="#d4956b",
    accent_red="#d46b6b",
    border_default="#2e2b22",
    border_focus="#d4a853",
    border_subtle="#242118",
    scroll_thumb="#3d3a3080",
    scroll_hover="#4d4a4080",
    shadow_color="#00000060",
)

AMBER_FONTS = ThemeFonts(
    display="'Libre Baskerville', 'Noto Serif SC', 'Georgia', serif",
    body="'Source Serif 4', 'Noto Serif SC', 'Georgia', serif",
    mono="'JetBrains Mono', 'Fira Code', monospace",
)

# -- Theme registry --------------------------------------------------
THEMES = {
    # New Apple-style themes
    "deep_purple_blue": (DEEP_PURPLE_BLUE, APPLE_FONTS),
    "minimal_apple": (MINIMAL_APPLE, APPLE_FONTS),
    # Warm amber theme
    "amber_gold": (AMBER_GOLD, AMBER_FONTS),
    # Legacy themes (kept for backward compatibility)
    "dark_professional": (DARK_PROFESSIONAL, DARK_FONTS),
    "minimal_white": (MINIMAL_WHITE, LIGHT_FONTS),
}


def get_theme(name: str) -> tuple[ThemeColors, ThemeFonts]:
    """Return (colors, fonts) for the named theme."""
    return THEMES.get(name, THEMES["deep_purple_blue"])
