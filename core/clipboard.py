"""Clipboard management with content preservation.

On X11, mouse-selected text is automatically available in the PRIMARY
selection — no Ctrl+C needed. We read PRIMARY first, fall back to
CLIPBOARD (explicitly copied text).
"""

import subprocess
import pyperclip


class ClipboardManager:
    """Manage clipboard with save/restore capability."""

    def __init__(self):
        self._saved_content: str | None = None

    def save(self):
        """Save current clipboard content."""
        try:
            self._saved_content = pyperclip.paste()
        except pyperclip.PyperclipException:
            self._saved_content = ""

    def restore(self):
        """Restore previously saved clipboard content."""
        if self._saved_content is not None:
            try:
                pyperclip.copy(self._saved_content)
            except pyperclip.PyperclipException:
                pass

    def get_selected_text(self) -> str:
        """Get text from clipboard (assumes user has copied selection).

        Saves clipboard first, reads content, then restores.
        """
        self.save()
        try:
            text = pyperclip.paste()
        except pyperclip.PyperclipException:
            text = ""
        return text.strip() if text else ""

    def get_text_and_restore(self) -> str:
        """Get clipboard text and immediately restore original content."""
        text = self.get_selected_text()
        self.restore()
        return text

    def get_selected_text_via_copy(self) -> str:
        """Read currently selected text without requiring manual Ctrl+C.

        On X11, reads the PRIMARY selection which automatically
        contains whatever text the user has highlighted with the mouse.
        Falls back to CLIPBOARD (explicitly copied text).
        """
        # Try X11 PRIMARY selection first (auto-selected text)
        try:
            result = subprocess.run(
                ["xclip", "-selection", "primary", "-o"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fall back to CLIPBOARD (manually copied text)
        return self.get_text_and_restore()
