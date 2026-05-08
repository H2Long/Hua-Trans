"""Text segmentation utilities for mixed CJK/Latin text."""


def is_cjk(ch: str) -> bool:
    """Check if a character is Chinese/Japanese/Korean."""
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0x20000 <= cp <= 0x2A6DF or 0xF900 <= cp <= 0xFAFF or
            0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF or  # Kana
            0xAC00 <= cp <= 0xD7AF)  # Hangul


def segment_text(text: str) -> list[tuple[bool, str]]:
    """Split text into (is_cjk, substring) alternating runs.

    Spaces and common punctuation are grouped with the preceding segment.
    """
    if not text:
        return []
    segments = []
    current = text[0]
    current_is_cjk = is_cjk(text[0])
    for ch in text[1:]:
        ch_is_cjk = is_cjk(ch)
        # Treat spaces/punctuation as belonging to previous segment
        if ch_is_cjk == current_is_cjk or ch.isspace() or ch in '.,;:!?()[]{}<>':
            current += ch
        else:
            segments.append((current_is_cjk, current))
            current = ch
            current_is_cjk = ch_is_cjk
    segments.append((current_is_cjk, current))
    return segments
