"""Sentence-by-sentence parallel display table for translation comparison."""

import re
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

from gui.theme import COLORS, FONTS, TABLE_WIDGET_STYLE


def split_sentences(text: str) -> list[str]:
    """Split text into sentences by common delimiters."""
    parts = re.split(r'(?<=[.?!。？！])\s*', text.strip())
    return [p for p in parts if p]


class SentencePairTable(QTableWidget):
    """Two-column table showing source and translated sentences side by side."""

    def __init__(self, parent=None):
        super().__init__(0, 2, parent)
        c = COLORS
        self.setHorizontalHeaderLabels(["原文", "译文"])
        self.setStyleSheet(TABLE_WIDGET_STYLE)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setWordWrap(True)

        # Column sizing: stretch both columns equally
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)

        # Row hover tracking
        self.setMouseTracking(True)
        self._hover_row = -1
        self._base_colors = {}

    def set_pairs(self, sources: list[str], translations: list[str]):
        """Populate the table with sentence pairs."""
        self.setRowCount(0)
        self._base_colors.clear()
        self._hover_row = -1

        count = max(len(sources), len(translations))
        self.setRowCount(count)

        c = COLORS
        for i in range(count):
            src = sources[i] if i < len(sources) else ""
            tgt = translations[i] if i < len(translations) else ""

            src_item = QTableWidgetItem(src)
            tgt_item = QTableWidgetItem(tgt)

            src_item.setForeground(QColor(c.text_primary))
            tgt_item.setForeground(QColor(c.text_primary))

            self.setItem(i, 0, src_item)
            self.setItem(i, 1, tgt_item)

            # Alternate row tint
            if i % 2 == 0:
                bg = QColor(c.bg_input)
            else:
                bg = QColor(c.bg_elevated)
            src_item.setBackground(bg)
            tgt_item.setBackground(bg)
            self._base_colors[i] = (bg, bg)

        # Auto-resize rows to content
        self.resizeRowsToContents()

    def animate_rows_in(self, delay_ms: int = 50):
        """Staggered fade-in: reveal rows one by one via timer."""
        count = self.rowCount()
        if count == 0:
            return

        # Hide all rows initially by setting height to 0
        for i in range(count):
            self.setRowHidden(i, True)

        self._reveal_index = 0

        def reveal_next():
            if self._reveal_index < self.rowCount():
                self.setRowHidden(self._reveal_index, False)
                self._reveal_index += 1
            else:
                self._reveal_timer.stop()

        self._reveal_timer = QTimer(self)
        self._reveal_timer.timeout.connect(reveal_next)
        self._reveal_timer.start(delay_ms)

    def mouseMoveEvent(self, event):
        """Highlight row under cursor."""
        row = self.rowAt(int(event.pos().y()))
        if row != self._hover_row:
            # Restore previous row
            if 0 <= self._hover_row < self.rowCount():
                self._restore_row_colors(self._hover_row)
            # Highlight new row
            if 0 <= row < self.rowCount():
                c = COLORS
                hover_bg = QColor(c.bg_hover)
                for col in range(2):
                    item = self.item(row, col)
                    if item:
                        item.setBackground(hover_bg)
            self._hover_row = row
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Clear hover highlight when mouse leaves."""
        if 0 <= self._hover_row < self.rowCount():
            self._restore_row_colors(self._hover_row)
        self._hover_row = -1
        super().leaveEvent(event)

    def _restore_row_colors(self, row: int):
        """Restore a row to its base alternating color."""
        if row in self._base_colors:
            src_bg, tgt_bg = self._base_colors[row]
            item0 = self.item(row, 0)
            item1 = self.item(row, 1)
            if item0:
                item0.setBackground(src_bg)
            if item1:
                item1.setBackground(tgt_bg)

    def reapply_theme(self):
        """Reapply styles after theme switch."""
        from gui.theme import TABLE_WIDGET_STYLE, COLORS as c
        self.setStyleSheet(TABLE_WIDGET_STYLE)
        # Recolor existing rows with new theme colors
        for i in range(self.rowCount()):
            if i % 2 == 0:
                bg = QColor(c.bg_input)
            else:
                bg = QColor(c.bg_elevated)
            self._base_colors[i] = (bg, bg)
            item0 = self.item(i, 0)
            item1 = self.item(i, 1)
            if item0:
                item0.setBackground(bg)
                item0.setForeground(QColor(c.text_primary))
            if item1:
                item1.setBackground(bg)
                item1.setForeground(QColor(c.text_primary))
