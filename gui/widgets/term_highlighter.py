"""Term highlighting engine — wraps matched EE terms in styled HTML spans."""

import html as html_module


class TermHighlighter:
    """Highlights EE terminology in QTextEdit via HTML generation.

    Pure data transformation — no QObject, no event filter, no thread issues.
    """

    def __init__(self, accent_green: str = "#4ec9b0", text_primary: str = "#cccccc"):
        self._term_map: dict[str, str] = {}
        self.accent_green = accent_green
        self.text_primary = text_primary

    def highlight(self, text: str, terminology) -> str:
        """Return HTML with matched terms wrapped in styled spans."""
        matches = terminology.lookup(text)
        if not matches:
            return self._plain_to_html(text)

        self._term_map = {}
        applied = []
        replaced_ranges = []

        for en, zh, start, end in matches:
            overlap = False
            for rs, re_ in replaced_ranges:
                if start < re_ and end > rs:
                    overlap = True
                    break
            if overlap:
                continue
            applied.append((en, zh, start, end))
            replaced_ranges.append((start, end))
            self._term_map[en.lower()] = zh

        g = self.accent_green
        parts = []
        prev_end = 0
        for en, zh, start, end in sorted(applied, key=lambda x: x[2]):
            if start > prev_end:
                parts.append(html_module.escape(text[prev_end:start]))
            escaped_en = html_module.escape(text[start:end])
            escaped_zh = html_module.escape(zh)
            parts.append(
                f'<span style="background-color: {g}20; '
                f'border-bottom: 1px dashed {g}; '
                f'color: {g}; padding: 1px 2px; border-radius: 2px;" '
                f'title="{escaped_zh}">{escaped_en}</span>'
            )
            prev_end = end

        if prev_end < len(text):
            parts.append(html_module.escape(text[prev_end:]))

        return self._wrap_html("".join(parts))

    def _plain_to_html(self, text: str) -> str:
        return self._wrap_html(html_module.escape(text).replace("\n", "<br>"))

    def _wrap_html(self, body: str) -> str:
        return (
            '<div style="font-family: JetBrains Mono, Cascadia Code, monospace; '
            f'font-size: 15px; line-height: 1.6; color: {self.text_primary}; '
            'padding: 4px;">'
            f'{body}'
            '</div>'
        )

    def get_term_map(self) -> dict[str, str]:
        """Return the current term map for external tooltip use."""
        return self._term_map.copy()
