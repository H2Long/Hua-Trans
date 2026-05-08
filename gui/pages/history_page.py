"""Translation history page — search, browse, export."""

import json
import csv
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QFrame, QFileDialog, QMessageBox,
    QHeaderView, QSplitter, QTextEdit, QAbstractItemView,
    QMenu, QAction, QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from gui.theme import (
    COLORS, FONTS, TABLE_WIDGET_STYLE, PUSH_BUTTON_STYLE,
    TEXT_EDIT_STYLE, SPLITTER_STYLE, LINE_EDIT_STYLE,
)
from gui.widgets.search_bar import SearchBar


class HistoryPage(QWidget):
    """Translation history with search and export."""

    fill_requested = pyqtSignal(str)  # emit source text to fill translation page

    def __init__(self, cache, parent=None):
        super().__init__(parent)
        self.cache = cache
        self._setup_ui()

    def _setup_ui(self):
        c = COLORS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        title = QLabel("翻译历史")
        title.setStyleSheet(f"""
            color: {c.text_bright};
            font-family: {FONTS.display};
            font-size: {FONTS.size_xxl}px;
            font-weight: 800;
        """)
        header_layout.addWidget(title)

        self._count_label = QLabel("0 条记录")
        self._count_label.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.mono};
            font-size: {FONTS.size_sm}px;
        """)
        header_layout.addWidget(self._count_label)

        header_layout.addStretch()

        export_btn = QPushButton("导出")
        export_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        export_btn.clicked.connect(self._export)
        header_layout.addWidget(export_btn)

        clear_btn = QPushButton("清空历史")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        clear_btn.clicked.connect(self._clear_history)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Search bar
        self._search = SearchBar("搜索翻译记录...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Splitter: table + detail
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(SPLITTER_STYLE)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["时间", "原文", "译文", "引擎"])
        self._table.setStyleSheet(TABLE_WIDGET_STYLE)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_table_context_menu)
        self._table.doubleClicked.connect(self._show_detail)
        self._table.setToolTip("双击查看详情 · 右键菜单更多操作")
        splitter.addWidget(self._table)

        # Detail panel
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(0, 10, 0, 0)
        detail_layout.setSpacing(8)

        detail_header = QLabel("详情")
        detail_header.setStyleSheet(f"""
            color: {c.text_secondary};
            font-family: {FONTS.display};
            font-size: {FONTS.size_sm}px;
            font-weight: 600;
        """)
        detail_layout.addWidget(detail_header)

        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setStyleSheet(TEXT_EDIT_STYLE)
        self._detail_text.setFont(QFont("SF Pro Text", 15))
        self._detail_text.setPlaceholderText("双击表格行查看详情...")
        detail_layout.addWidget(self._detail_text)

        splitter.addWidget(detail)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter, 1)

        # Load data
        self.refresh()

    def refresh(self):
        """Reload history data."""
        query = self._search.text()
        if query:
            records = self.cache.search_history(query)
        else:
            records = self.cache.get_history(limit=200)

        self._populate_table(records)
        self._count_label.setText(f"{len(records)} 条记录")

    def _populate_table(self, records: list[dict]):
        self._table.setRowCount(len(records))
        for i, rec in enumerate(records):
            # Time
            ts = rec.get("created_at", 0)
            time_str = datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else ""
            self._table.setItem(i, 0, QTableWidgetItem(time_str))

            # Source (truncated)
            src = rec.get("source_text", "")
            src_item = QTableWidgetItem(src[:80] + ("..." if len(src) > 80 else ""))
            src_item.setData(Qt.ItemDataRole.UserRole, rec)
            self._table.setItem(i, 1, src_item)

            # Translation (truncated)
            trans = rec.get("translated_text", "")
            self._table.setItem(i, 2, QTableWidgetItem(trans[:80] + ("..." if len(trans) > 80 else "")))

            # Engine
            self._table.setItem(i, 3, QTableWidgetItem(rec.get("engine", "")))

    def _on_search(self, query: str):
        self.refresh()

    def _on_table_context_menu(self, pos):
        """Right-click context menu for history table rows."""
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        item = self._table.item(row, 1)
        if not item:
            return
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return

        menu = QMenu(self)
        retranslate_action = QAction("重新翻译", self)
        retranslate_action.triggered.connect(
            lambda: self.fill_requested.emit(rec.get("source_text", ""))
        )
        menu.addAction(retranslate_action)

        copy_action = QAction("复制译文", self)
        copy_action.triggered.connect(
            lambda: QApplication.clipboard().setText(rec.get("translated_text", ""))
        )
        menu.addAction(copy_action)

        menu.addSeparator()

        detail_action = QAction("查看详情", self)
        detail_action.triggered.connect(lambda: self._show_detail(self._table.model().index(row, 0)))
        menu.addAction(detail_action)

        menu.exec_(self._table.viewport().mapToGlobal(pos))

    def _show_detail(self, index):
        row = index.row()
        item = self._table.item(row, 1)
        if not item:
            return
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return

        ts = rec.get("created_at", 0)
        time_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else ""
        detail = (
            f"时间: {time_str}\n"
            f"引擎: {rec.get('engine', '')}\n"
            f"语言: {rec.get('source_lang', '')} → {rec.get('target_lang', '')}\n"
            f"{'─' * 50}\n\n"
            f"原文:\n{rec.get('source_text', '')}\n\n"
            f"{'─' * 50}\n\n"
            f"译文:\n{rec.get('translated_text', '')}"
        )
        self._detail_text.setPlainText(detail)

        # Emit source text so main window can fill translation page
        self.fill_requested.emit(rec.get("source_text", ""))

    def _export(self):
        path, filt = QFileDialog.getSaveFileName(
            self, "导出历史", "translation_history",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        if not path:
            return

        fmt = "csv" if path.endswith(".csv") else "json"
        data = self.cache.export_history(fmt)

        with open(path, "w", encoding="utf-8") as f:
            f.write(data)

        QMessageBox.information(self, "导出成功", f"已导出到: {path}")

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有翻译历史吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cache.clear()
            self.refresh()

    def add_record(self):
        """Called when a new translation is completed."""
        self.refresh()

    def reapply_theme(self):
        """Reapply styles after theme switch without losing state."""
        from gui.theme import (
            COLORS as c, FONTS, TABLE_WIDGET_STYLE, PUSH_BUTTON_STYLE,
            TEXT_EDIT_STYLE, SPLITTER_STYLE, LINE_EDIT_STYLE,
        )
        self._table.setStyleSheet(TABLE_WIDGET_STYLE)
        self._detail_text.setStyleSheet(TEXT_EDIT_STYLE)
