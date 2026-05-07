"""Terminology management page — CRUD for EE terms."""

import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QDialog, QFormLayout, QLineEdit,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from gui.theme import (
    COLORS, FONTS, TABLE_WIDGET_STYLE, PUSH_BUTTON_STYLE,
    LINE_EDIT_STYLE,
)
from gui.widgets.search_bar import SearchBar


class _AddTermDialog(QDialog):
    """Dialog for adding or editing a term."""

    def __init__(self, en: str = "", zh: str = "", parent=None):
        super().__init__(parent)
        c = COLORS
        self.setWindowTitle("添加术语" if not en else "编辑术语")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{
                background: {c.bg_surface};
            }}
            QLabel {{
                color: {c.text_primary};
                font-family: {FONTS.body};
                font-size: {FONTS.size_md}px;
            }}
        """)

        layout = QFormLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        self._en_input = QLineEdit(en)
        self._en_input.setStyleSheet(LINE_EDIT_STYLE)
        self._en_input.setPlaceholderText("English term")
        layout.addRow("英文术语:", self._en_input)

        self._zh_input = QLineEdit(zh)
        self._zh_input.setStyleSheet(LINE_EDIT_STYLE)
        self._zh_input.setPlaceholderText("中文翻译")
        layout.addRow("中文翻译:", self._zh_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet(PUSH_BUTTON_STYLE)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self) -> tuple[str, str]:
        return self._en_input.text().strip(), self._zh_input.text().strip()


class TerminologyPage(QWidget):
    """Terminology management with search, add, edit, delete, import/export."""

    def __init__(self, terminology, parent=None):
        super().__init__(parent)
        self.terminology = terminology
        self._setup_ui()

    def _setup_ui(self):
        c = COLORS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        title = QLabel("术语管理")
        title.setStyleSheet(f"""
            color: {c.text_bright};
            font-family: {FONTS.display};
            font-size: {FONTS.size_xxl}px;
            font-weight: 800;
        """)
        header_layout.addWidget(title)

        self._count_label = QLabel("0 个术语")
        self._count_label.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.mono};
            font-size: {FONTS.size_sm}px;
        """)
        header_layout.addWidget(self._count_label)

        header_layout.addStretch()

        add_btn = QPushButton("添加术语")
        add_btn.setObjectName("primaryButton")
        add_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        add_btn.clicked.connect(self._add_term)
        header_layout.addWidget(add_btn)

        import_btn = QPushButton("导入 JSON")
        import_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        import_btn.clicked.connect(self._import_json)
        header_layout.addWidget(import_btn)

        export_btn = QPushButton("导出 JSON")
        export_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        export_btn.clicked.connect(self._export_json)
        header_layout.addWidget(export_btn)

        reset_btn = QPushButton("重置为内置术语")
        reset_btn.setObjectName("dangerButton")
        reset_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        reset_btn.clicked.connect(self._reset_terms)
        header_layout.addWidget(reset_btn)

        layout.addLayout(header_layout)

        # Search bar
        self._search = SearchBar("搜索术语...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["English", "中文"])
        self._table.setStyleSheet(TABLE_WIDGET_STYLE)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(self._edit_term)
        layout.addWidget(self._table, 1)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        edit_btn.clicked.connect(self._edit_term)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("dangerButton")
        delete_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        delete_btn.clicked.connect(self._delete_term)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Load data
        self.refresh()

    def refresh(self):
        """Reload terminology data."""
        query = self._search.text().lower()
        all_terms = self.terminology.get_all_terms()

        if query:
            filtered = {k: v for k, v in all_terms.items()
                        if query in k.lower() or query in v.lower()}
        else:
            filtered = all_terms

        sorted_terms = sorted(filtered.items(), key=lambda x: x[0].lower())
        self._populate_table(sorted_terms)
        self._count_label.setText(f"{len(all_terms)} 个术语")

    def _populate_table(self, terms: list[tuple[str, str]]):
        self._table.setRowCount(len(terms))
        for i, (en, zh) in enumerate(terms):
            en_item = QTableWidgetItem(en)
            en_item.setData(Qt.ItemDataRole.UserRole, en)
            self._table.setItem(i, 0, en_item)
            self._table.setItem(i, 1, QTableWidgetItem(zh))

    def _on_search(self, query: str):
        self.refresh()

    def _get_selected_term(self) -> str | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self._table.item(rows[0].row(), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add_term(self):
        dialog = _AddTermDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            en, zh = dialog.get_values()
            if en and zh:
                self.terminology.add_term(en, zh)
                self.refresh()

    def _edit_term(self):
        en = self._get_selected_term()
        if not en:
            return
        zh = self.terminology.terms.get(en, "")
        dialog = _AddTermDialog(en, zh, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_en, new_zh = dialog.get_values()
            if new_en and new_zh:
                if new_en != en:
                    self.terminology.remove_term(en)
                self.terminology.add_term(new_en, new_zh)
                self.refresh()

    def _delete_term(self):
        en = self._get_selected_term()
        if not en:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除术语 \"{en}\" 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.terminology.remove_term(en)
            self.refresh()

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入术语", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                QMessageBox.warning(self, "格式错误", "JSON 文件应为 {\"en\": \"zh\"} 格式")
                return

            # Conflict detection: check if new terms overlap with existing ones
            existing = self.terminology.get_all_terms()
            conflicts = []
            for new_en in data:
                if not isinstance(data[new_en], str):
                    continue
                for exist_en in existing:
                    if new_en != exist_en and (
                        new_en.lower() in exist_en.lower()
                        or exist_en.lower() in new_en.lower()
                    ):
                        conflicts.append((new_en, data[new_en], exist_en, existing[exist_en]))
                        break

            if conflicts:
                conflict_msg = "检测到以下术语可能重叠:\n\n"
                for new_en, new_zh, exist_en, exist_zh in conflicts[:10]:
                    conflict_msg += f"  • 导入: \"{new_en}\" → \"{new_zh}\"\n"
                    conflict_msg += f"    已有: \"{exist_en}\" → \"{exist_zh}\"\n\n"
                if len(conflicts) > 10:
                    conflict_msg += f"  ... 还有 {len(conflicts) - 10} 个冲突\n"
                conflict_msg += "\n是否仍然导入？"
                reply = QMessageBox.question(
                    self, "术语重叠警告", conflict_msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            count = 0
            for en, zh in data.items():
                if isinstance(zh, str):
                    self.terminology.add_term(en, zh)
                    count += 1
            self.refresh()
            QMessageBox.information(self, "导入成功", f"已导入 {count} 个术语")
        except Exception as e:
            QMessageBox.warning(self, "导入失败", str(e))

    def _reset_terms(self):
        """Reset all terms to built-in defaults."""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要删除所有自定义术语，恢复内置的 356 条默认术语吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.terminology.reset_to_defaults()
            self.refresh()
            QMessageBox.information(self, "已重置", "术语已恢复为内置默认")

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出术语", "terminology.json", "JSON Files (*.json)"
        )
        if not path:
            return
        data = self.terminology.get_all_terms()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        QMessageBox.information(self, "导出成功", f"已导出到: {path}")

    def reapply_theme(self):
        """Reapply styles after theme switch without losing state."""
        from gui.theme import TABLE_WIDGET_STYLE, PUSH_BUTTON_STYLE, LINE_EDIT_STYLE
        self._table.setStyleSheet(TABLE_WIDGET_STYLE)
