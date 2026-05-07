"""Runtime hotkey manager — register/unregister global hotkeys.

Uses pynput (X11) on Linux — no root required, unlike the keyboard library.
"""

import threading

# pynput key format: <ctrl>+<shift>+t
# keyboard library format: ctrl+shift+t
# We accept user-friendly format and convert internally.


def _to_pynput_format(hotkey: str) -> str:
    """Convert 'ctrl+shift+t' to '<ctrl>+<shift>+t' for pynput.

    Single-character keys stay bare (t, a, 1). Named keys get angle brackets
    (backspace, enter, space, f1, etc.). Modifiers always get angle brackets.
    """
    parts = hotkey.lower().replace(" ", "").split("+")
    out = []
    for p in parts:
        if not p:
            continue
        if len(p) == 1:
            out.append(p)
        else:
            out.append(f"<{p}>")
    return "+".join(out)


def _from_pynput_format(hotkey: str) -> str:
    """Convert '<ctrl>+<shift>+t' back to 'ctrl+shift+t'."""
    return hotkey.replace("<", "").replace(">", "")


class HotkeyManager:
    """Manage global hotkey registration at runtime using pynput.

    Wraps pynput.keyboard.GlobalHotKeys to support changing hotkeys
    without restarting the application.
    """

    def __init__(self):
        self._current_hotkey: str | None = None
        self._callback = None
        self._lock = threading.Lock()
        self._listener = None
        self._pynput = None
        try:
            from pynput.keyboard import GlobalHotKeys
            self._GlobalHotKeys = GlobalHotKeys
            self._pynput = True
        except ImportError:
            self._GlobalHotKeys = None
            self._pynput = False

    def is_available(self) -> bool:
        return self._pynput is not None

    def register(self, hotkey: str, callback) -> tuple[bool, str]:
        """Register a new hotkey, unregistering the old one.

        Returns (success, message).
        """
        with self._lock:
            if not self._pynput:
                return False, "pynput 未安装。请运行: pip install pynput"

            # Stop old listener
            self._stop_listener()

            try:
                pynput_hotkey = _to_pynput_format(hotkey)
                self._listener = self._GlobalHotKeys({
                    pynput_hotkey: callback,
                })
                self._listener.start()
                self._current_hotkey = hotkey
                self._callback = callback
                return True, f"热键已注册: {hotkey}"
            except Exception as e:
                return False, f"注册失败: {e}"

    def _stop_listener(self):
        """Stop the current pynput listener if running."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def unregister(self):
        """Unregister the current hotkey."""
        with self._lock:
            self._stop_listener()
            self._current_hotkey = None

    def get_current_hotkey(self) -> str | None:
        return self._current_hotkey


def normalize_hotkey(hotkey: str) -> str:
    """Normalize a hotkey string for display.

    Converts user-friendly format to a consistent format.
    """
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
    parts_normalized = modifiers + [key]
    return "+".join(parts_normalized)


def validate_hotkey(hotkey: str) -> tuple[bool, str]:
    """Validate a hotkey string.

    Returns (valid, message).
    """
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
