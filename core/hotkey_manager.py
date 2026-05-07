"""Global hotkey manager using X11 XGrabKey — no root required.

Replaces pynput (which needs root for evdev) with python-xlib's XGrabKey
which works through the standard X11 protocol as a normal user.
"""

import threading
import re

# ── Key name mappings ──────────────────────────────────────────────────────
_KEY_SYM_MAP = {
    # Letters
    **{chr(c): chr(c) for c in range(ord('a'), ord('z') + 1)},
    **{chr(c): chr(c) for c in range(ord('A'), ord('Z') + 1)},
    # Digits
    **{str(d): str(d) for d in range(10)},
    # Function keys
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
    "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
    "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
    # Special keys
    "space": "space", "enter": "Return", "return": "Return",
    "escape": "Escape", "esc": "Escape",
    "tab": "Tab", "backspace": "BackSpace",
    "delete": "Delete", "insert": "Insert",
    "home": "Home", "end": "End",
    "pageup": "Prior", "pagedown": "Next",
    "up": "Up", "down": "Down", "left": "Left", "right": "Right",
    # Numpad
    "kp_0": "KP_0", "kp_1": "KP_1", "kp_2": "KP_2", "kp_3": "KP_3",
    "kp_4": "KP_4", "kp_5": "KP_5", "kp_6": "KP_6", "kp_7": "KP_7",
    "kp_8": "KP_8", "kp_9": "KP_9",
    # Punctuation
    "-": "minus", "=": "equal", "[": "bracketleft", "]": "bracketright",
    "\\": "backslash", ";": "semicolon", "'": "apostrophe",
    ",": "comma", ".": "period", "/": "slash", "`": "grave",
    # Special chars (use their uppercase mapping)
    "!": "exclam", "@": "at", "#": "numbersign", "$": "dollar",
    "%": "percent", "^": "asciicircum", "&": "ampersand",
    "*": "asterisk", "(": "parenleft", ")": "parenright",
    "_": "underscore", "+": "plus",
    "{": "braceleft", "}": "braceright",
    "|": "bar", ":": "colon", "\"": "quotedbl",
    "<": "less", ">": "greater", "?": "question",
    "~": "asciitilde",
}


def _parse_hotkey(hotkey: str) -> tuple[int, int]:
    """Parse 'ctrl+shift+t' → (modifier_mask, keycode).

    Returns (0, 0) if X11 is unavailable or parsing fails.
    """
    try:
        from Xlib import X, XK
    except ImportError:
        return (0, 0)

    parts = [p.strip() for p in hotkey.lower().split("+") if p.strip()]
    if len(parts) < 2:
        return (0, 0)

    modifier_map = {
        "ctrl": X.ControlMask, "control": X.ControlMask,
        "alt": X.Mod1Mask,
        "shift": X.ShiftMask,
        "win": X.Mod4Mask, "super": X.Mod4Mask, "meta": X.Mod4Mask,
    }
    mask = 0
    key_name = None

    for p in parts:
        if p in modifier_map:
            mask |= modifier_map[p]
        else:
            key_name = p

    if not key_name or key_name not in _KEY_SYM_MAP:
        return (0, 0)

    keysym_str = _KEY_SYM_MAP[key_name]
    keysym = XK.string_to_keysym(keysym_str)
    if keysym == 0:
        return (0, 0)

    # We need a display to look up the keycode. Use a temporary connection.
    try:
        from Xlib.display import Display
        d = Display()
        keycode = d.keysym_to_keycode(keysym)
        d.close()
        return (mask, keycode)
    except Exception:
        return (0, 0)


class HotkeyManager:
    """Manage global hotkey via X11 XGrabKey — no root required."""

    def __init__(self):
        self._current_keycode: tuple[int, int] | None = None
        self._callback = None
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False
        self._available = False
        try:
            from Xlib.display import Display
            from Xlib import X
            self._Display = Display
            self._X = X
            self._available = True
        except ImportError:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def register(self, hotkey: str, callback) -> tuple[bool, str]:
        """Register a new hotkey, replacing any previous one.

        Returns (success, message).
        """
        with self._lock:
            if not self._available:
                return False, "python-xlib 未安装。请运行: pip install python-xlib"

            mask, keycode = _parse_hotkey(hotkey)
            if keycode == 0:
                return False, f"无法解析快捷键: {hotkey}"

            self._stop()

            try:
                self._display = self._Display()
                root = self._display.screen().root
                root.grab_key(keycode, mask, 1, self._X.GrabModeAsync, self._X.GrabModeAsync)
                root.grab_key(keycode, mask | self._X.Mod2Mask, 1,  # NumLock
                              self._X.GrabModeAsync, self._X.GrabModeAsync)
                root.grab_key(keycode, mask | self._X.LockMask, 1,  # CapsLock
                              self._X.GrabModeAsync, self._X.GrabModeAsync)
                root.grab_key(keycode, mask | self._X.Mod2Mask | self._X.LockMask, 1,
                              self._X.GrabModeAsync, self._X.GrabModeAsync)
                self._display.flush()
            except Exception as e:
                self._display = None
                return False, f"注册失败: {e}"

            self._current_keycode = (mask, keycode)
            self._callback = callback
            self._running = True
            self._thread = threading.Thread(target=self._event_loop, daemon=True)
            self._thread.start()
            return True, f"热键已注册: {hotkey}"

    def _event_loop(self):
        """Listen for X11 key press events in a background thread."""
        try:
            while self._running:
                event = self._display.next_event()
                if event.type == self._X.KeyPress and self._callback:
                    self._callback()
        except Exception:
            pass

    def _stop(self):
        self._running = False
        if self._display is not None:
            try:
                if self._current_keycode is not None:
                    mask, keycode = self._current_keycode
                    root = self._display.screen().root
                    root.ungrab_key(keycode, mask, root)
                    root.ungrab_key(keycode, mask | self._X.Mod2Mask, root)
                    root.ungrab_key(keycode, mask | self._X.LockMask, root)
                    root.ungrab_key(keycode, mask | self._X.Mod2Mask | self._X.LockMask, root)
                    self._display.flush()
            except Exception:
                pass
            try:
                self._display.close()
            except Exception:
                pass
            self._display = None
        self._current_keycode = None
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1)
        self._thread = None

    def unregister(self):
        """Unregister the current hotkey and stop the event loop."""
        with self._lock:
            self._stop()

    def get_current_hotkey(self) -> str | None:
        return None  # We don't track the original string


def normalize_hotkey(hotkey: str) -> str:
    """Normalize a hotkey string for display."""
    parts = hotkey.lower().replace(" ", "").split("+")
    modifiers = []
    key = None
    for part in parts:
        if part in ("ctrl", "alt", "shift", "win", "super", "meta"):
            modifiers.append(part)
        else:
            key = part
    if not key:
        return hotkey
    mod_map = {"super": "win", "meta": "win"}
    modifiers = [mod_map.get(m, m) for m in modifiers]
    return "+".join(modifiers + [key])


def validate_hotkey(hotkey: str) -> tuple[bool, str]:
    """Validate a hotkey string."""
    if not hotkey or not hotkey.strip():
        return False, "快捷键不能为空"
    parts = hotkey.lower().replace(" ", "").split("+")
    if len(parts) < 2:
        return False, "快捷键需要至少一个修饰键和一个普通键"
    modifiers = {"ctrl", "alt", "shift", "win", "super", "meta"}
    has_modifier = any(p in modifiers for p in parts)
    if not has_modifier:
        return False, "需要至少一个修饰键 (Ctrl/Alt/Shift)"
    return True, "有效"
