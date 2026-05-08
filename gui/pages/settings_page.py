"""Settings page — API keys, hotkey, theme, font, cache, OCR, color customization."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
    QSlider, QCheckBox, QScrollArea, QMessageBox, QFrame,
    QColorDialog, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QKeyEvent, QColor

from gui.theme import (
    COLORS, FONTS, PUSH_BUTTON_STYLE, COMBO_BOX_STYLE,
    SPIN_BOX_STYLE, LINE_EDIT_STYLE, GROUP_BOX_STYLE,
    SLIDER_STYLE, CHECK_BOX_STYLE,
)
from core.config import save_config, store_api_key, delete_api_key
from core.hotkey_manager import validate_hotkey


_MODIFIER_KEYS = {
    Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
    Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R,
    Qt.Key.Key_Meta,
}

_MODIFIER_NAMES = {
    Qt.Key.Key_Control: "Ctrl",
    Qt.Key.Key_Shift: "Shift",
    Qt.Key.Key_Alt: "Alt",
    Qt.Key.Key_Meta: "Win",
    Qt.Key.Key_Super_L: "Win",
    Qt.Key.Key_Super_R: "Win",
}

_KEY_NAMES = {
    Qt.Key.Key_Space: "Space", Qt.Key.Key_Return: "Enter",
    Qt.Key.Key_Enter: "Enter", Qt.Key.Key_Escape: "Esc",
    Qt.Key.Key_Tab: "Tab", Qt.Key.Key_Backspace: "Backspace",
    Qt.Key.Key_Delete: "Delete", Qt.Key.Key_Insert: "Insert",
    Qt.Key.Key_Home: "Home", Qt.Key.Key_End: "End",
    Qt.Key.Key_PageUp: "PageUp", Qt.Key.Key_PageDown: "PageDown",
    Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down",
    Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right",
    Qt.Key.Key_F1: "F1", Qt.Key.Key_F2: "F2", Qt.Key.Key_F3: "F3",
    Qt.Key.Key_F4: "F4", Qt.Key.Key_F5: "F5", Qt.Key.Key_F6: "F6",
    Qt.Key.Key_F7: "F7", Qt.Key.Key_F8: "F8", Qt.Key.Key_F9: "F9",
    Qt.Key.Key_F10: "F10", Qt.Key.Key_F11: "F11", Qt.Key.Key_F12: "F12",
}


class HotkeyRecorder(QLineEdit):
    """Input field that records key combinations when focused.

    Click to start recording, press desired key combo, click away to stop.
    """

    hotkey_recorded = pyqtSignal(str)

    def __init__(self, current_hotkey: str = "", parent=None):
        super().__init__(current_hotkey, parent)
        self._recording = False
        self._pressed_modifiers: set[str] = set()
        self._pressed_key: str | None = None
        self._previous_text = current_hotkey
        self.setReadOnly(True)
        self.setPlaceholderText("点击后按下快捷键...")
        self._update_style()

    def _update_style(self):
        c = COLORS
        if self._recording:
            self.setStyleSheet(f"""
                QLineEdit {{
                    background: {c.bg_input};
                    color: {c.accent_orange};
                    border: 2px solid {c.accent_orange};
                    border-radius: 10px;
                    padding: 10px 14px;
                    font-family: {FONTS.mono};
                    font-size: {FONTS.size_md}px;
                }}
            """)
        else:
            self.setStyleSheet(LINE_EDIT_STYLE)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._start_recording()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._stop_recording()

    def _start_recording(self):
        self._recording = True
        self._previous_text = self.text()
        self._pressed_modifiers.clear()
        self._pressed_key = None
        self.setText("按下快捷键...")
        self._update_style()

    def _stop_recording(self):
        if self._recording and self._pressed_key:
            combo = self._build_combo()
            self.setText(combo)
            self.hotkey_recorded.emit(combo)
        elif self._recording and not self._pressed_key:
            self.setText(self._previous_text)
        self._recording = False
        self._update_style()

    def _build_combo(self) -> str:
        parts = []
        for mod in ("Ctrl", "Alt", "Shift", "Win"):
            if mod.lower() in {m.lower() for m in self._pressed_modifiers}:
                parts.append(mod)
        if self._pressed_key:
            parts.append(self._pressed_key)
        return "+".join(parts)

    def keyPressEvent(self, event: QKeyEvent):
        if not self._recording:
            super().keyPressEvent(event)
            return

        key = event.key()

        # Track modifiers
        if key in _MODIFIER_KEYS:
            mod_name = _MODIFIER_NAMES.get(key, "")
            if mod_name:
                self._pressed_modifiers.add(mod_name)
            self.setText(self._build_combo() + "+..." if self._pressed_modifiers else "按下快捷键...")
            return

        # Track regular key
        key_name = _KEY_NAMES.get(key)
        if not key_name:
            if 32 <= key <= 126:
                key_name = chr(key).upper()
            else:
                key_name = f"Key({key})"

        self._pressed_key = key_name
        combo = self._build_combo()
        self.setText(combo)

    def keyReleaseEvent(self, event: QKeyEvent):
        if not self._recording:
            super().keyReleaseEvent(event)
            return
        # Don't stop on modifier release — wait for focus out

    def reapply_theme(self):
        """Reapply styles after theme switch."""
        self._update_style()


class SettingsPage(QWidget):
    """Application settings with grouped form layout."""

    theme_changed = pyqtSignal(str)
    hotkey_changed = pyqtSignal(str)

    def __init__(self, config, translator, cache, parent=None):
        super().__init__(parent)
        self.config = config
        self.translator = translator
        self.cache = cache
        self._setup_ui()

    def _setup_ui(self):
        c = COLORS
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {c.bg_base};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: {c.bg_base};
            }}
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("设置")
        title.setStyleSheet(f"""
            color: {c.text_bright};
            font-family: {FONTS.display};
            font-size: {FONTS.size_xxl}px;
            font-weight: 800;
        """)
        layout.addWidget(title)

        # -- Translation Engine ----------------------------------------
        engine_group = self._create_group("翻译引擎")
        engine_form = QFormLayout()
        engine_form.setSpacing(12)

        self._engine_combo = QComboBox()
        self._engine_combo.addItems(["google", "deepl", "llm"])
        self._engine_combo.setStyleSheet(COMBO_BOX_STYLE)
        self._engine_combo.setCurrentText(self.config.get("translation_engine", "google"))
        engine_form.addRow("默认引擎:", self._engine_combo)

        self._deepl_key = QLineEdit(self.config.get("deepl_api_key", ""))
        self._deepl_key.setStyleSheet(LINE_EDIT_STYLE)
        self._deepl_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._deepl_key.setPlaceholderText("DeepL API Key")
        engine_form.addRow("DeepL Key:", self._deepl_key)

        self._llm_key = QLineEdit(self.config.get("llm_api_key", ""))
        self._llm_key.setStyleSheet(LINE_EDIT_STYLE)
        self._llm_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._llm_key.setPlaceholderText("LLM API Key")
        engine_form.addRow("LLM Key:", self._llm_key)

        self._llm_url = QLineEdit(self.config.get("llm_base_url", "https://api.anthropic.com"))
        self._llm_url.setStyleSheet(LINE_EDIT_STYLE)
        engine_form.addRow("LLM URL:", self._llm_url)

        self._llm_model = QLineEdit(self.config.get("llm_model", "claude-sonnet-4-20250514"))
        self._llm_model.setStyleSheet(LINE_EDIT_STYLE)
        engine_form.addRow("LLM Model:", self._llm_model)

        engine_group.setLayout(engine_form)
        layout.addWidget(engine_group)

        # -- Languages -------------------------------------------------
        lang_group = self._create_group("语言")
        lang_form = QFormLayout()
        lang_form.setSpacing(12)

        self._src_lang = QComboBox()
        self._src_lang.addItems(["English", "中文"])
        self._src_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._src_lang.setCurrentIndex(0 if self.config.get("source_lang", "en") == "en" else 1)
        lang_form.addRow("源语言:", self._src_lang)

        self._tgt_lang = QComboBox()
        self._tgt_lang.addItems(["中文", "English"])
        self._tgt_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._tgt_lang.setCurrentIndex(0 if self.config.get("target_lang", "zh") == "zh" else 1)
        lang_form.addRow("目标语言:", self._tgt_lang)

        lang_group.setLayout(lang_form)
        layout.addWidget(lang_group)

        # -- Hotkey ----------------------------------------------------
        hotkey_group = self._create_group("快捷键")
        hotkey_form = QFormLayout()
        hotkey_form.setSpacing(12)

        self._hotkey_recorder = HotkeyRecorder(self.config.get("hotkey", "ctrl+shift+t"))
        self._hotkey_recorder.hotkey_recorded.connect(self._on_hotkey_recorded)
        hotkey_form.addRow("翻译热键:", self._hotkey_recorder)

        hotkey_hint = QLabel("点击输入框后按下想要的快捷键组合，点击别处确认")
        hotkey_hint.setStyleSheet(f"color: {c.text_dim}; font-size: {FONTS.size_xs}px; font-family: {FONTS.body};")
        hotkey_hint.setWordWrap(True)
        hotkey_form.addRow("", hotkey_hint)

        hotkey_group.setLayout(hotkey_form)
        layout.addWidget(hotkey_group)

        # -- Appearance ------------------------------------------------
        appear_group = self._create_group("外观")
        appear_form = QFormLayout()
        appear_form.setSpacing(12)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["deep_purple_blue", "minimal_apple", "amber_gold", "dark_professional", "minimal_white"])
        self._theme_combo.setStyleSheet(COMBO_BOX_STYLE)
        self._theme_combo.setCurrentText(self.config.get("theme", "deep_purple_blue"))
        appear_form.addRow("主题:", self._theme_combo)

        self._font_size = QSpinBox()
        self._font_size.setRange(10, 24)
        self._font_size.setValue(self.config.get("font_size", 14))
        self._font_size.setStyleSheet(SPIN_BOX_STYLE)
        appear_form.addRow("字体大小:", self._font_size)

        appear_group.setLayout(appear_form)
        layout.addWidget(appear_group)

        # -- Theme Color Customization ---------------------------------
        color_group = self._create_group("主题色")
        color_layout = QVBoxLayout()
        color_layout.setSpacing(12)

        # Current accent color display + pick button
        color_row = QHBoxLayout()
        color_row.setSpacing(12)

        self._color_preview = QFrame()
        self._color_preview.setFixedSize(36, 36)
        accent = self.config.get("custom_accent_color", c.accent_blue)
        self._color_preview.setStyleSheet(f"""
            QFrame {{
                background: {accent};
                border-radius: 8px;
                border: 1px solid {c.border_default};
            }}
        """)
        color_row.addWidget(self._color_preview)

        self._color_label = QLabel(f"当前: {accent}")
        self._color_label.setStyleSheet(f"""
            color: {c.text_primary};
            font-family: {FONTS.mono};
            font-size: {FONTS.size_sm}px;
        """)
        color_row.addWidget(self._color_label)

        color_row.addStretch()

        pick_btn = QPushButton("选择颜色")
        pick_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        pick_btn.clicked.connect(self._pick_accent_color)
        color_row.addWidget(pick_btn)

        reset_color_btn = QPushButton("恢复默认")
        reset_color_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        reset_color_btn.clicked.connect(self._reset_accent_color)
        color_row.addWidget(reset_color_btn)

        color_layout.addLayout(color_row)

        # Preset colors
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)

        preset_label = QLabel("预设:")
        preset_label.setStyleSheet(f"color: {c.text_secondary}; font-family: {FONTS.body}; font-size: {FONTS.size_sm}px;")
        preset_layout.addWidget(preset_label)

        presets = [
            ("#7C6CFA", "薰衣草紫蓝"),
            ("#6e5ce7", "深紫"),
            ("#4FC3F7", "天蓝"),
            ("#5fd4b8", "薄荷绿"),
            ("#F5C469", "琥珀金"),
            ("#F08CA0", "珊瑚粉"),
            ("#0078d4", "经典蓝"),
        ]
        for hex_color, name in presets:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setToolTip(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {hex_color};
                    border: 2px solid {c.border_default};
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border-color: {c.text_bright};
                }}
            """)
            btn.clicked.connect(lambda checked, hc=hex_color: self._apply_preset_color(hc))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        color_layout.addLayout(preset_layout)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # -- Floating Popup --------------------------------------------
        popup_group = self._create_group("悬浮窗")
        popup_form = QFormLayout()
        popup_form.setSpacing(12)

        self._popup_width = QSpinBox()
        self._popup_width.setRange(300, 800)
        self._popup_width.setValue(self.config.get("popup_width", 450))
        self._popup_width.setStyleSheet(SPIN_BOX_STYLE)
        popup_form.addRow("宽度:", self._popup_width)

        self._popup_opacity = QSpinBox()
        self._popup_opacity.setRange(50, 100)
        self._popup_opacity.setValue(int(self.config.get("popup_opacity", 0.95) * 100))
        self._popup_opacity.setSuffix("%")
        self._popup_opacity.setStyleSheet(SPIN_BOX_STYLE)
        popup_form.addRow("不透明度:", self._popup_opacity)

        self._auto_hide = QSpinBox()
        self._auto_hide.setRange(0, 60)
        self._auto_hide.setValue(self.config.get("auto_hide_seconds", 10))
        self._auto_hide.setSuffix(" 秒")
        self._auto_hide.setStyleSheet(SPIN_BOX_STYLE)
        popup_form.addRow("自动隐藏:", self._auto_hide)

        self._popup_mini = QCheckBox("紧凑模式（仅显示译文，更小更轻量）")
        self._popup_mini.setStyleSheet(CHECK_BOX_STYLE)
        self._popup_mini.setChecked(self.config.get("popup_mini_mode", False))
        popup_form.addRow(self._popup_mini)

        popup_group.setLayout(popup_form)
        layout.addWidget(popup_group)

        # -- Cache -----------------------------------------------------
        cache_group = self._create_group("缓存")
        cache_form = QFormLayout()
        cache_form.setSpacing(12)

        self._cache_enabled = QCheckBox("启用翻译缓存")
        self._cache_enabled.setStyleSheet(CHECK_BOX_STYLE)
        self._cache_enabled.setChecked(self.config.get("cache_enabled", True))
        cache_form.addRow(self._cache_enabled)

        self._cache_days = QSpinBox()
        self._cache_days.setRange(1, 365)
        self._cache_days.setValue(self.config.get("cache_max_days", 30))
        self._cache_days.setSuffix(" 天")
        self._cache_days.setStyleSheet(SPIN_BOX_STYLE)
        cache_form.addRow("缓存保留:", self._cache_days)

        cache_stats = self.cache.stats()
        stats_label = QLabel(f"当前缓存: {cache_stats['total_entries']} 条记录")
        stats_label.setStyleSheet(f"color: {c.text_dim}; font-size: {FONTS.size_sm}px; font-family: {FONTS.body};")
        cache_form.addRow(stats_label)

        clear_cache_btn = QPushButton("清空缓存")
        clear_cache_btn.setObjectName("dangerButton")
        clear_cache_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        clear_cache_btn.clicked.connect(self._clear_cache)
        cache_form.addRow(clear_cache_btn)

        cache_group.setLayout(cache_form)
        layout.addWidget(cache_group)

        # -- OCR -------------------------------------------------------
        ocr_group = self._create_group("OCR")
        ocr_form = QFormLayout()
        ocr_form.setSpacing(12)

        self._ocr_lang = QComboBox()
        self._ocr_lang.addItems(["eng", "chi_sim", "chi_tra", "jpn", "kor", "deu", "fra"])
        self._ocr_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._ocr_lang.setCurrentText(self.config.get("ocr_language", "eng"))
        ocr_form.addRow("OCR 语言:", self._ocr_lang)

        ocr_group.setLayout(ocr_form)
        layout.addWidget(ocr_group)

        # -- Terminology -----------------------------------------------
        term_group = self._create_group("术语")
        term_form = QFormLayout()
        term_form.setSpacing(12)

        self._term_highlight = QCheckBox("翻译结果中高亮术语")
        self._term_highlight.setStyleSheet(CHECK_BOX_STYLE)
        self._term_highlight.setChecked(self.config.get("terminology_highlight", True))
        term_form.addRow(self._term_highlight)

        term_group.setLayout(term_form)
        layout.addWidget(term_group)

        # -- Diagnostics -----------------------------------------------
        diag_group = self._create_group("诊断")
        diag_layout = QHBoxLayout()
        diag_layout.setSpacing(12)

        diag_label = QLabel("导出应用日志用于问题排查")
        diag_label.setStyleSheet(f"color: {c.text_secondary}; font-family: {FONTS.body}; font-size: {FONTS.size_sm}px;")
        diag_layout.addWidget(diag_label)
        diag_layout.addStretch()

        export_log_btn = QPushButton("导出诊断日志")
        export_log_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        export_log_btn.clicked.connect(self._export_diagnostics)
        diag_layout.addWidget(export_log_btn)

        diag_group.setLayout(diag_layout)
        layout.addWidget(diag_group)

        # -- Action buttons --------------------------------------------
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)

        reset_btn = QPushButton("恢复默认")
        reset_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()

        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("primaryButton")
        save_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _create_group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setStyleSheet(GROUP_BOX_STYLE)
        return group

    def _pick_accent_color(self):
        """Open color dialog to pick custom accent color."""
        c = COLORS
        current = self.config.get("custom_accent_color", c.accent_blue)
        color = QColorDialog.getColor(
            QColor(current), self, "选择主题色",
            QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if color.isValid():
            hex_color = color.name()
            self._apply_preset_color(hex_color)

    def _apply_preset_color(self, hex_color: str):
        """Apply a color as the accent color."""
        c = COLORS
        self.config["custom_accent_color"] = hex_color
        self._color_preview.setStyleSheet(f"""
            QFrame {{
                background: {hex_color};
                border-radius: 8px;
                border: 1px solid {c.border_default};
            }}
        """)
        self._color_label.setText(f"当前: {hex_color}")

        # Apply to theme
        from gui.theme import set_accent_color
        set_accent_color(hex_color)

    def _reset_accent_color(self):
        """Reset accent color to theme default."""
        from gui.theme import get_active_theme_name
        from gui.colors import THEMES
        theme_name = get_active_theme_name()
        default_color = THEMES[theme_name][0].accent_blue
        self.config.pop("custom_accent_color", None)
        self._apply_preset_color(default_color)

    def _on_hotkey_recorded(self, hotkey: str):
        """Handle hotkey recording from the recorder widget."""
        valid, msg = validate_hotkey(hotkey)
        if not valid:
            QMessageBox.warning(self, "无效快捷键", msg)
            self._hotkey_recorder.setText(self.config.get("hotkey", "ctrl+shift+t"))
            return
        self.config["hotkey"] = hotkey
        # Immediately register so user doesn't need to click "保存设置"
        self.hotkey_changed.emit(hotkey)

    def _save(self):
        """Save all settings to config."""
        self.config["translation_engine"] = self._engine_combo.currentText()
        self.config["deepl_api_key"] = self._deepl_key.text()
        self.config["llm_api_key"] = self._llm_key.text()
        self.config["llm_base_url"] = self._llm_url.text()
        self.config["llm_model"] = self._llm_model.text()
        self.config["source_lang"] = "zh" if self._src_lang.currentIndex() == 1 else "en"
        self.config["target_lang"] = "en" if self._tgt_lang.currentIndex() == 1 else "zh"
        self.config["font_size"] = self._font_size.value()
        self.config["popup_width"] = self._popup_width.value()
        self.config["popup_opacity"] = self._popup_opacity.value() / 100.0
        self.config["popup_mini_mode"] = self._popup_mini.isChecked()
        self.config["auto_hide_seconds"] = self._auto_hide.value()
        self.config["cache_enabled"] = self._cache_enabled.isChecked()
        self.config["cache_max_days"] = self._cache_days.value()
        self.config["ocr_language"] = self._ocr_lang.currentText()
        self.config["terminology_highlight"] = self._term_highlight.isChecked()

        # Hotkey change
        new_hotkey = self._hotkey_recorder.text().strip()
        if new_hotkey and new_hotkey != self.config.get("hotkey"):
            valid, msg = validate_hotkey(new_hotkey)
            if valid:
                self.config["hotkey"] = new_hotkey
                self.hotkey_changed.emit(new_hotkey)

        # Theme change
        new_theme = self._theme_combo.currentText()
        if new_theme != self.config.get("theme"):
            self.config["theme"] = new_theme
            self.theme_changed.emit(new_theme)

        # Persist API keys to OS keychain
        deepl_key = self._deepl_key.text().strip()
        llm_key = self._llm_key.text().strip()
        if deepl_key:
            store_api_key("deepl_api_key", deepl_key)
        else:
            delete_api_key("deepl_api_key")
        if llm_key:
            store_api_key("llm_api_key", llm_key)
        else:
            delete_api_key("llm_api_key")

        save_config(self.config)
        self.translator.reload_engines()

        QMessageBox.information(self, "保存成功", "设置已保存")

    def _export_diagnostics(self):
        """Export application log to a user-chosen file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出诊断日志", "hua-trans-diagnostics.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if not path:
            return
        try:
            from core.logging_setup import export_diagnostics, get_log_path
            log_content = export_diagnostics()
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Hua-Trans Diagnostic Report\n")
                f.write(f"{'=' * 50}\n")
                f.write(f"Log file: {get_log_path()}\n\n")
                f.write(log_content)
            QMessageBox.information(self, "导出成功", f"诊断日志已保存到: {path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))

    def _clear_cache(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有缓存吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cache.clear()
            stats = self.cache.stats()
            QMessageBox.information(self, "已清空", f"缓存已清空")

    def _reset_defaults(self):
        reply = QMessageBox.question(
            self, "确认恢复",
            "确定要恢复所有默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from core.config import DEFAULT_CONFIG
            self.config.update(DEFAULT_CONFIG)
            save_config(self.config)
            QMessageBox.information(self, "已恢复", "设置已恢复为默认值，请重启应用")

    def reapply_theme(self):
        """Reapply styles after theme switch without losing state."""
        from gui.theme import (
            COLORS as c, PUSH_BUTTON_STYLE, COMBO_BOX_STYLE,
            SPIN_BOX_STYLE, LINE_EDIT_STYLE, GROUP_BOX_STYLE,
            CHECK_BOX_STYLE,
        )
        self._engine_combo.setStyleSheet(COMBO_BOX_STYLE)
        self._deepl_key.setStyleSheet(LINE_EDIT_STYLE)
        self._llm_key.setStyleSheet(LINE_EDIT_STYLE)
        self._llm_url.setStyleSheet(LINE_EDIT_STYLE)
        self._llm_model.setStyleSheet(LINE_EDIT_STYLE)
        self._src_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._tgt_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._theme_combo.setStyleSheet(COMBO_BOX_STYLE)
        self._font_size.setStyleSheet(SPIN_BOX_STYLE)
        self._popup_width.setStyleSheet(SPIN_BOX_STYLE)
        self._popup_opacity.setStyleSheet(SPIN_BOX_STYLE)
        self._auto_hide.setStyleSheet(SPIN_BOX_STYLE)
        self._cache_enabled.setStyleSheet(CHECK_BOX_STYLE)
        self._cache_days.setStyleSheet(SPIN_BOX_STYLE)
        self._ocr_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._term_highlight.setStyleSheet(CHECK_BOX_STYLE)
        self._popup_mini.setStyleSheet(CHECK_BOX_STYLE)
        self._hotkey_recorder.reapply_theme()
