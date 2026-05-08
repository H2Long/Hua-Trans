"""Global hotkey manager — platform-aware backend selection.

Linux:   python-xlib XGrabKey (no root required)
Windows: pynput GlobalHotKeys
"""

import sys
import threading
import re

# ── Key name mappings (platform-independent) ───────────────────────────────
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
    # Special chars
    "!": "exclam", "@": "at", "#": "numbersign", "$": "dollar",
    "%": "percent", "^": "asciicircum", "&": "ampersand",
    "*": "asterisk", "(": "parenleft", ")": "parenright",
    "_": "underscore", "+": "plus",
    "{": "braceleft", "}": "braceright",
    "|": "bar", ":": "colon", "\"": "quotedbl",
    "<": "less", ">": "greater", "?": "question",
    "~": "asciitilde",
}


# ═══════════════════════════════════════════════════════════════════════════
# Linux backend: X11 XGrabKey via python-xlib
# ═══════════════════════════════════════════════════════════════════════════
class _X11HotkeyBackend:
    """Hotkey via X11 XGrabKey — no root required."""

    def __init__(self):
        self._current_keycode = None
        self._callback = None
        self._lock = threading.Lock()
        self._thread = None
        self._running = False
        self._display = None
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
        with self._lock:
            if not self._available:
                return False, "python-xlib 未安装。请运行: pip install python-xlib"

            mask, keycode = self._parse_hotkey(hotkey)
            if keycode == 0:
                return False, f"无法解析快捷键: {hotkey}"

            self._stop()

            try:
                self._display = self._Display()
                root = self._display.screen().root
                mods = [mask,
                        mask | self._X.Mod2Mask,  # NumLock
                        mask | self._X.LockMask,   # CapsLock
                        mask | self._X.Mod2Mask | self._X.LockMask]
                for m in mods:
                    root.grab_key(keycode, m, 1,
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

    def _parse_hotkey(self, hotkey: str) -> tuple[int, int]:
        """Parse 'ctrl+shift+t' → (modifier_mask, keycode)."""
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

        try:
            from Xlib.display import Display
            d = Display()
            keycode = d.keysym_to_keycode(keysym)
            d.close()
            return (mask, keycode)
        except Exception:
            return (0, 0)

    def _event_loop(self):
        """Listen for X11 key press events in a background thread."""
        reconnect_attempts = 0
        while self._running:
            try:
                event = self._display.next_event()
                if event.type == self._X.KeyPress and self._callback:
                    self._callback()
                reconnect_attempts = 0
            except Exception as e:
                reconnect_attempts += 1
                if reconnect_attempts > 3:
                    print(f"[Hotkey] X11 event loop failed after {reconnect_attempts} attempts: {e}",
                          file=sys.stderr)
                    break
                print(f"[Hotkey] X11 connection lost, reconnecting ({reconnect_attempts}/3)...",
                      file=sys.stderr)
                try:
                    self._display.close()
                except Exception:
                    pass
                try:
                    self._display = self._Display()
                    root = self._display.screen().root
                    mask, keycode = self._current_keycode
                    mods = [mask,
                            mask | self._X.Mod2Mask,
                            mask | self._X.LockMask,
                            mask | self._X.Mod2Mask | self._X.LockMask]
                    for m in mods:
                        root.grab_key(keycode, m, 1,
                                      self._X.GrabModeAsync, self._X.GrabModeAsync)
                    self._display.flush()
                except Exception as reconnect_error:
                    print(f"[Hotkey] Reconnect failed: {reconnect_error}", file=sys.stderr)

    def _stop(self):
        self._running = False
        if self._display is not None:
            try:
                if self._current_keycode is not None:
                    mask, keycode = self._current_keycode
                    root = self._display.screen().root
                    mods = [mask,
                            mask | self._X.Mod2Mask,
                            mask | self._X.LockMask,
                            mask | self._X.Mod2Mask | self._X.LockMask]
                    for m in mods:
                        root.ungrab_key(keycode, m, root)
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
        with self._lock:
            self._stop()


# ═══════════════════════════════════════════════════════════════════════════
# Windows backend: pynput GlobalHotKeys
# ═══════════════════════════════════════════════════════════════════════════
class _PynputHotkeyBackend:
    """Hotkey via pynput.keyboard.GlobalHotKeys — native on Windows."""

    def __init__(self):
        self._hotkey_obj = None
        self._callback = None
        self._available = False
        try:
            from pynput import keyboard as _kb
            self._keyboard = _kb
            self._available = True
        except ImportError:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def register(self, hotkey: str, callback) -> tuple[bool, str]:
        if not self._available:
            return False, "pynput 未安装。请运行: pip install pynput"

        pynput_hotkey = self._convert_hotkey(hotkey)
        if not pynput_hotkey:
            return False, f"无法解析快捷键: {hotkey}"

        self._stop()
        try:
            self._hotkey_obj = self._keyboard.GlobalHotKeys({
                pynput_hotkey: callback,
            })
            self._hotkey_obj.start()
            self._callback = callback
            return True, f"热键已注册: {hotkey}"
        except Exception as e:
            return False, f"注册失败: {e}"

    def _convert_hotkey(self, hotkey: str) -> str:
        """Convert 'ctrl+shift+t' → '<ctrl>+<shift>+t' for pynput."""
        parts = [p.strip() for p in hotkey.lower().split("+") if p.strip()]
        if len(parts) < 2:
            return ""
        converted = []
        for p in parts:
            if p in ("ctrl", "control", "alt", "shift", "win", "super", "meta"):
                # pynput uses <ctrl>, <alt>, <shift>, <cmd> for win
                tag = "cmd" if p in ("win", "super", "meta") else p
                converted.append(f"<{tag}>")
            else:
                converted.append(p)
        return "+".join(converted)

    def _stop(self):
        if self._hotkey_obj is not None:
            try:
                self._hotkey_obj.stop()
            except Exception:
                pass
            self._hotkey_obj = None

    def unregister(self):
        self._stop()


# ═══════════════════════════════════════════════════════════════════════════
# Facade: HotkeyManager — picks the right backend for the current platform
# ═══════════════════════════════════════════════════════════════════════════
class HotkeyManager:
    """Manage global hotkey — platform-aware backend selection."""

    def __init__(self):
        if sys.platform == "win32":
            self._backend = _PynputHotkeyBackend()
        else:
            self._backend = _X11HotkeyBackend()

    def is_available(self) -> bool:
        return self._backend.is_available()

    def register(self, hotkey: str, callback) -> tuple[bool, str]:
        """Register a new hotkey, replacing any previous one.

        Returns (success, message).
        """
        return self._backend.register(hotkey, callback)

    def unregister(self):
        """Unregister the current hotkey and stop the event loop."""
        self._backend.unregister()

    def get_current_hotkey(self) -> str | None:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Platform-independent utilities
# ═══════════════════════════════════════════════════════════════════════════
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
