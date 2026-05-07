"""Translation page — PDF reader + translation engine."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QListWidget, QListWidgetItem, QLabel, QPushButton,
    QFileDialog, QComboBox, QTabWidget, QSpinBox, QFrame,
    QMessageBox, QProgressDialog, QApplication, QMenu, QAction,
    QLineEdit,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent, QTextCursor

from gui.theme import (
    COLORS, FONTS, TEXT_EDIT_STYLE, LIST_WIDGET_STYLE,
    COMBO_BOX_STYLE, PUSH_BUTTON_STYLE, TAB_WIDGET_STYLE,
    SPLITTER_STYLE, SPIN_BOX_STYLE,
)
from gui.widgets.term_highlighter import TermHighlighter


class TranslationWorker(QThread):
    """Background thread for translation."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, manager, text, engine=None, cache=None,
                 source_lang="en", target_lang="zh"):
        super().__init__()
        self.manager = manager
        self.text = text
        self.engine = engine
        self.cache = cache
        self.source_lang = source_lang
        self.target_lang = target_lang

    def run(self):
        try:
            if self.isInterruptionRequested():
                return
            if self.cache:
                engine = self.engine or self.manager.config.get("translation_engine", "google")
                cached = self.cache.get(
                    self.text, engine, self.source_lang, self.target_lang,
                )
                if cached:
                    self.finished.emit({
                        "original": self.text,
                        "translated": cached,
                        "engine": engine,
                        "terms_applied": [],
                        "from_cache": True,
                    })
                    return

            if self.isInterruptionRequested():
                return
            result = self.manager.translate(
                self.text, self.engine, self.source_lang, self.target_lang,
            )
            result["from_cache"] = False

            if self.isInterruptionRequested():
                return
            if self.cache:
                self.cache.put(
                    result["original"], result["translated"],
                    result["engine"], self.source_lang, self.target_lang,
                )
            self.finished.emit(result)
        except Exception as e:
            if not self.isInterruptionRequested():
                self.error.emit(str(e))


class TranslationPage(QWidget):
    """Main translation view with PDF reader and translation panel."""

    status_message = pyqtSignal(str)
    translation_done = pyqtSignal(str, str, str)  # original, translated, engine

    def __init__(self, config, terminology, translator, cache, ocr, parent=None):
        super().__init__(parent)
        self.config = config
        self.terminology = terminology
        self.translator = translator
        self.cache = cache
        self.ocr = ocr
        self.pdf = None  # Lazy import
        self._current_page = 0
        self._worker = None
        self._highlighter = TermHighlighter(
            accent_green=COLORS.accent_green,
            text_primary=COLORS.text_primary,
        )

        self._init_pdf_handler()
        self._setup_ui()
        self.setAcceptDrops(True)

    def _init_pdf_handler(self):
        from core.pdf_handler import PDFHandler
        self.pdf = PDFHandler()

    def _setup_ui(self):
        c = COLORS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # -- Top-level mode switch: Translation / PDF Reading ---------
        self._mode_tabs = QTabWidget()
        self._mode_tabs.setStyleSheet(TAB_WIDGET_STYLE)

        # == Tab 0: Translation =======================================
        trans_tab = QWidget()
        trans_layout = QVBoxLayout(trans_tab)
        trans_layout.setContentsMargins(24, 16, 24, 20)
        trans_layout.setSpacing(10)

        # Page title
        trans_title = QLabel("翻译")
        trans_title.setStyleSheet(f"""
            color: {c.text_bright};
            font-family: {FONTS.display};
            font-size: 26px;
            font-weight: 800;
            padding-bottom: 2px;
        """)
        trans_layout.addWidget(trans_title)

        # Language selector row
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(10)

        self._source_lang = QComboBox()
        self._source_lang.addItems(["English", "中文"])
        self._source_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._source_lang.setCurrentIndex(0 if self.config.get("source_lang", "en") == "en" else 1)
        lang_layout.addWidget(self._source_lang)

        swap_btn = QPushButton("⇄")
        swap_btn.setFixedSize(40, 36)
        swap_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        swap_btn.setToolTip("交换源语言和目标语言")
        swap_btn.clicked.connect(self._swap_languages)
        lang_layout.addWidget(swap_btn)

        self._target_lang = QComboBox()
        self._target_lang.addItems(["中文", "English"])
        self._target_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._target_lang.setCurrentIndex(0 if self.config.get("target_lang", "zh") == "zh" else 1)
        lang_layout.addWidget(self._target_lang)

        lang_layout.addStretch()
        trans_layout.addLayout(lang_layout)

        # Source text input
        source_label = QLabel("输入文本")
        source_label.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.display};
            font-size: {FONTS.size_xs}px;
            letter-spacing: 1px;
        """)
        trans_layout.addWidget(source_label)

        self._source_edit = QTextEdit()
        self._source_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_input};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-left: 3px solid {c.accent_blue}40;
                border-radius: 10px;
                padding: 12px;
                font-family: 'SF Pro Text', sans-serif;
                font-size: {FONTS.size_md}px;
                selection-background-color: {c.accent_blue}40;
            }}
            QTextEdit:focus {{ border-color: {c.accent_blue}; border-left-color: {c.accent_blue}; }}
        """)
        self._source_edit.setFont(QFont("SF Pro Text", FONTS.size_md))
        self._source_edit.setMaximumHeight(180)
        self._source_edit.setPlaceholderText("在此粘贴英文文本... 或使用 Ctrl+Return 热键翻译")
        trans_layout.addWidget(self._source_edit)

        # Engine selector row with inline translate button
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)

        engine_label = QLabel("引擎:")
        engine_label.setStyleSheet(f"""
            color: {c.text_secondary};
            font-family: {FONTS.display};
            font-size: {FONTS.size_sm}px;
            font-weight: 600;
        """)
        ctrl_layout.addWidget(engine_label)

        self._engine_combo = QComboBox()
        self._engine_combo.setStyleSheet(COMBO_BOX_STYLE)
        self._engine_combo.addItems(["google", "deepl", "llm"])
        ctrl_layout.addWidget(self._engine_combo)

        ctrl_layout.addStretch()

        # Toggle button for parallel view
        self._toggle_pair_btn = QPushButton("并排对照")
        self._toggle_pair_btn.setCheckable(True)
        self._toggle_pair_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        self._toggle_pair_btn.toggled.connect(self._toggle_pair_view)
        ctrl_layout.addWidget(self._toggle_pair_btn)

        # Inline translate button
        self._float_btn = QPushButton("翻译")
        self._float_btn.setObjectName("successButton")
        self._float_btn.setShortcut("Ctrl+Return")
        self._float_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        self._float_btn.clicked.connect(self._do_translate)
        ctrl_layout.addWidget(self._float_btn)

        # Cancel button (hidden, shown during translation)
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setObjectName("dangerButton")
        self._cancel_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        self._cancel_btn.clicked.connect(self._cancel_translation)
        self._cancel_btn.hide()
        ctrl_layout.addWidget(self._cancel_btn)

        trans_layout.addLayout(ctrl_layout)

        # Separator between input and output
        sep_line = QFrame()
        sep_line.setFixedHeight(1)
        sep_line.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.3 {c.border_default},
                    stop:0.7 {c.border_default}, stop:1 transparent);
                margin: 4px 0;
            }}
        """)
        trans_layout.addWidget(sep_line)

        # Translation result
        self._result_label = QLabel("翻译结果")
        self._result_label.setStyleSheet(f"""
            color: {c.text_dim};
            font-family: {FONTS.display};
            font-size: {FONTS.size_xs}px;
            letter-spacing: 1px;
        """)
        trans_layout.addWidget(self._result_label)

        self._result_edit = QTextEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-left: 3px solid {c.accent_green}40;
                border-radius: 10px;
                padding: 16px;
                font-family: 'SF Pro Text', 'Noto Sans SC', sans-serif;
                font-size: 17px;
                line-height: 1.8;
                selection-background-color: {c.accent_green}30;
            }}
            QTextEdit:focus {{
                border-color: {c.accent_green};
                border-left-color: {c.accent_green};
            }}
        """)
        self._result_edit.setFont(QFont("SF Pro Text", FONTS.size_lg))
        self._result_edit.setPlaceholderText("翻译结果将在此显示...")
        trans_layout.addWidget(self._result_edit, 1)

        # Sentence pair table (P2, initially hidden)
        from gui.widgets.sentence_pair_table import SentencePairTable
        self._pair_table = SentencePairTable()
        self._pair_table.setVisible(False)
        trans_layout.addWidget(self._pair_table, 1)

        # Terms applied label
        self._terms_label = QLabel("")
        self._terms_label.setStyleSheet(f"""
            color: {c.accent_green};
            font-family: {FONTS.mono};
            font-size: {FONTS.size_xs}px;
            padding: 4px 0;
        """)
        trans_layout.addWidget(self._terms_label)

        self._mode_tabs.addTab(trans_tab, "翻译")

        # == Tab 1: PDF Reading =======================================
        pdf_tab = QWidget()
        pdf_layout = QVBoxLayout(pdf_tab)
        pdf_layout.setContentsMargins(16, 12, 16, 16)
        pdf_layout.setSpacing(12)

        # PDF control bar (moved from toolbar)
        pdf_bar = QFrame()
        pdf_bar.setStyleSheet(f"""
            QFrame {{
                background: {c.bg_surface};
                border: 1px solid {c.border_default};
                border-radius: 10px;
            }}
        """)
        bar_layout = QHBoxLayout(pdf_bar)
        bar_layout.setContentsMargins(12, 6, 12, 6)
        bar_layout.setSpacing(10)

        open_btn = QPushButton("打开 PDF")
        open_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        open_btn.clicked.connect(self._open_pdf)
        bar_layout.addWidget(open_btn)

        bar_layout.addSpacing(10)

        self._page_label = QLabel("未加载文件")
        self._page_label.setStyleSheet(f"""
            color: {c.text_secondary};
            font-family: {FONTS.body};
            font-size: {FONTS.size_sm}px;
        """)
        bar_layout.addWidget(self._page_label)

        bar_layout.addSpacing(14)

        page_lbl = QLabel("页码:")
        page_lbl.setStyleSheet(f"color: {c.text_secondary}; font-size: {FONTS.size_sm}px; font-family: {FONTS.body};")
        bar_layout.addWidget(page_lbl)

        self._page_spin = QSpinBox()
        self._page_spin.setMinimum(1)
        self._page_spin.setMaximum(1)
        self._page_spin.setFixedWidth(60)
        self._page_spin.setStyleSheet(SPIN_BOX_STYLE)
        self._page_spin.valueChanged.connect(self._goto_page)
        bar_layout.addWidget(self._page_spin)

        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(36, 36)
        prev_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        prev_btn.clicked.connect(self._prev_page)
        bar_layout.addWidget(prev_btn)

        next_btn = QPushButton(">")
        next_btn.setFixedSize(36, 36)
        next_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        next_btn.clicked.connect(self._next_page)
        bar_layout.addWidget(next_btn)

        bar_layout.addStretch()

        translate_page_btn = QPushButton("翻译整页")
        translate_page_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        translate_page_btn.clicked.connect(self._translate_current_page)
        bar_layout.addWidget(translate_page_btn)

        self._ocr_btn = QPushButton("OCR 扫描")
        self._ocr_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        self._ocr_btn.clicked.connect(self._ocr_current_page)
        bar_layout.addWidget(self._ocr_btn)

        overlay_btn = QPushButton("原位翻译")
        overlay_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        overlay_btn.clicked.connect(self._overlay_translate)
        bar_layout.addWidget(overlay_btn)

        pdf_layout.addWidget(pdf_bar)

        # PDF search bar (hidden, shown on Ctrl+F)
        self._pdf_search_bar = QFrame()
        self._pdf_search_bar.setStyleSheet(f"""
            QFrame {{
                background: {c.bg_surface};
                border: 1px solid {c.accent_blue};
                border-radius: 8px;
            }}
        """)
        search_layout = QHBoxLayout(self._pdf_search_bar)
        search_layout.setContentsMargins(8, 4, 8, 4)
        search_layout.setSpacing(6)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(f"font-size: 12px; border: none; background: transparent;")
        search_layout.addWidget(search_icon)
        self._pdf_search_input = QLineEdit()
        self._pdf_search_input.setPlaceholderText("搜索 PDF 内容...")
        self._pdf_search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {c.bg_input};
                color: {c.text_primary};
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: {FONTS.size_sm}px;
            }}
        """)
        self._pdf_search_input.returnPressed.connect(self._pdf_search_next)
        self._pdf_search_input.textChanged.connect(self._pdf_search_next)
        search_layout.addWidget(self._pdf_search_input)
        match_label = QLabel("")
        match_label.setStyleSheet(f"color: {c.text_dim}; font-size: 10px; border: none; background: transparent;")
        self._pdf_search_match = match_label
        search_layout.addWidget(match_label)
        self._pdf_search_bar.hide()
        pdf_layout.addWidget(self._pdf_search_bar)

        # PDF content tabs (TOC + content)
        self._pdf_tabs = QTabWidget()
        pdf_tabs = self._pdf_tabs
        pdf_tabs.setStyleSheet(TAB_WIDGET_STYLE)

        self._toc_list = QListWidget()
        self._toc_list.setStyleSheet(f"""
            QListWidget {{
                background: {c.bg_input};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 10px;
                padding: 6px;
                font-family: {FONTS.body};
                font-size: {FONTS.size_sm}px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 8px;
                margin: 2px 0;
                border-left: 3px solid transparent;
            }}
            QListWidget::item:hover {{
                background: {c.bg_hover};
                border-left-color: {c.accent_blue};
            }}
            QListWidget::item:selected {{
                background: {c.bg_active};
                color: {c.text_bright};
                border-left-color: {c.accent_blue};
            }}
        """)
        self._toc_list.itemClicked.connect(self._toc_clicked)
        pdf_tabs.addTab(self._toc_list, "目录")

        self._pdf_text = QTextEdit()
        self._pdf_text.setReadOnly(True)
        self._pdf_text.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._pdf_text.customContextMenuRequested.connect(self._pdf_context_menu)
        self._pdf_text.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 10px;
                padding: 16px;
                font-family: 'SF Pro Text', 'Noto Sans SC', sans-serif;
                font-size: 14px;
                line-height: 1.7;
                selection-background-color: {c.accent_blue}40;
            }}
        """)
        self._pdf_text.setFont(QFont("SF Pro Text", 14))
        pdf_tabs.addTab(self._pdf_text, "内容")

        # -- Page image tab (original PDF rendering) --------------------
        from PyQt5.QtWidgets import QScrollArea
        from PyQt5.QtGui import QPixmap

        self._image_scroll = QScrollArea()
        self._image_scroll.setWidgetResizable(False)
        self._image_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: #2a2a2a;
                border: 1px solid {c.border_default};
                border-radius: 10px;
            }}
        """)
        self._page_image_label = QLabel("加载 PDF 后显示原始页面")
        self._page_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_image_label.setStyleSheet(f"""
            QLabel {{
                color: {c.text_dim};
                font-family: {FONTS.body};
                font-size: {FONTS.size_sm}px;
                padding: 40px;
                background: #2a2a2a;
            }}
        """)
        self._image_scroll.setWidget(self._page_image_label)
        pdf_tabs.addTab(self._image_scroll, "原始页面")

        # -- Side-by-side view (original image | extracted text) -------
        side_by_side = QWidget()
        side_layout = QHBoxLayout(side_by_side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(8)

        # Left: page image
        self._side_image_scroll = QScrollArea()
        self._side_image_scroll.setWidgetResizable(False)
        self._side_image_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._side_image_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: #2a2a2a;
                border: 1px solid {c.border_default};
                border-radius: 10px;
            }}
        """)
        self._side_image_label = QLabel("原始页面")
        self._side_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._side_image_label.setStyleSheet(f"""
            QLabel {{
                color: {c.text_dim};
                font-family: {FONTS.body};
                font-size: {FONTS.size_xs}px;
                padding: 20px;
                background: #2a2a2a;
            }}
        """)
        self._side_image_scroll.setWidget(self._side_image_label)

        # Re-scale side image when panel resizes
        def _on_side_resize(event):
            if hasattr(self, '_side_full_pixmap') and self._side_full_pixmap:
                w = self._side_image_scroll.viewport().width() - 4
                if w > 100:
                    scaled = self._side_full_pixmap.scaledToWidth(w, Qt.TransformationMode.SmoothTransformation)
                    self._side_image_label.setPixmap(scaled)
                    self._side_image_label.setFixedSize(scaled.size())

        self._side_image_scroll.resizeEvent = _on_side_resize
        side_layout.addWidget(self._side_image_scroll, 1)

        # Right: extracted text
        self._side_text = QTextEdit()
        self._side_text.setReadOnly(True)
        self._side_text.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 10px;
                padding: 12px;
                font-family: 'SF Pro Text', 'Noto Sans SC', sans-serif;
                font-size: 14px;
                line-height: 1.7;
            }}
        """)
        side_layout.addWidget(self._side_text, 1)
        pdf_tabs.addTab(side_by_side, "对照")

        # -- In-place translation overlay tab (side-by-side) ----------
        overlay_side = QWidget()
        overlay_side_layout = QHBoxLayout(overlay_side)
        overlay_side_layout.setContentsMargins(0, 0, 0, 0)
        overlay_side_layout.setSpacing(8)

        # Left: original page image
        self._overlay_orig_scroll = QScrollArea()
        self._overlay_orig_scroll.setWidgetResizable(False)
        self._overlay_orig_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay_orig_scroll.setStyleSheet(f"""
            QScrollArea {{ background: #2a2a2a; border: 1px solid {c.border_default}; border-radius: 10px; }}
        """)
        self._overlay_orig_label = QLabel("原始页面")
        self._overlay_orig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay_orig_label.setStyleSheet(f"color: {c.text_dim}; padding: 20px; background: #2a2a2a;")
        self._overlay_orig_scroll.setWidget(self._overlay_orig_label)
        overlay_side_layout.addWidget(self._overlay_orig_scroll, 1)

        # Right: translated overlay
        self._overlay_scroll = QScrollArea()
        self._overlay_scroll.setWidgetResizable(False)
        self._overlay_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay_scroll.setStyleSheet(f"""
            QScrollArea {{ background: #1a1a1a; border: 1px solid {c.border_default}; border-radius: 10px; }}
        """)
        self._overlay_label = QLabel("点击「原位翻译」开始")
        self._overlay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay_label.setStyleSheet(f"color: {c.text_dim}; padding: 20px; background: #1a1a1a;")
        self._overlay_scroll.setWidget(self._overlay_label)
        overlay_side_layout.addWidget(self._overlay_scroll, 1)

        pdf_tabs.addTab(overlay_side, "原位翻译")

        pdf_layout.addWidget(pdf_tabs, 1)
        self._mode_tabs.addTab(pdf_tab, "PDF 阅读")

        layout.addWidget(self._mode_tabs, 1)

    def _swap_languages(self):
        """Swap source and target languages."""
        src_text = self._source_lang.currentText()
        tgt_text = self._target_lang.currentText()
        self._source_lang.setCurrentText(tgt_text)
        self._target_lang.setCurrentText(src_text)

    def _get_lang_code(self, combo) -> str:
        """Get language code from combo box text."""
        text = combo.currentText()
        return "zh" if text == "中文" else "en"

    def _toggle_pair_view(self, checked: bool):
        """Toggle between result text and sentence pair table."""
        self._pair_table.setVisible(checked)
        self._result_edit.setVisible(not checked)
        self._result_label.setText("并排对照" if checked else "翻译结果")

    def _open_pdf(self):
        # Close previous dialog if open
        if hasattr(self, '_file_dlg') and self._file_dlg is not None:
            self._file_dlg.close()
            self._file_dlg = None

        # Use independent window (non-modal) with high-contrast light styling
        dlg = QFileDialog(None, "打开 PDF", "", "PDF Files (*.pdf);;All Files (*)")
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dlg.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self._file_dlg = dlg
        dlg.setStyleSheet("""
            QFileDialog, QWidget {
                background: #f5f5f7;
                color: #1d1d1f;
            }
            QLabel {
                color: #1d1d1f;
                font-size: 14px;
            }
            QLineEdit {
                background: #ffffff;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 14px;
            }
            QPushButton {
                background: #ffffff;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #e8e8ed;
                border-color: #6e5ce7;
            }
            QListView, QTreeView {
                background: #ffffff;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                alternate-background-color: #f5f5f7;
            }
            QListView::item:selected, QTreeView::item:selected {
                background: #6e5ce7;
                color: #ffffff;
            }
            QListView::item:hover, QTreeView::item:hover {
                background: #e8e8ed;
            }
            QComboBox {
                background: #ffffff;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QHeaderView::section {
                background: #f5f5f7;
                color: #1d1d1f;
                border: none;
                border-bottom: 1px solid #d2d2d7;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QToolButton {
                background: transparent;
                color: #1d1d1f;
                border: none;
            }
            QToolButton:hover {
                background: #e8e8ed;
            }
            QSidebar {
                background: #f5f5f7;
            }
        """)
        dlg.resize(800, 520)
        dlg.fileSelected.connect(self._load_pdf)
        dlg.show()

        def _on_dlg_destroyed():
            self._file_dlg = None
        dlg.destroyed.connect(_on_dlg_destroyed)

    def _load_pdf(self, path: str):
        if not self.pdf.open(path):
            QMessageBox.warning(self, "错误", f"无法打开: {path}")
            return

        filename = path.split("/")[-1]
        self._page_label.setText(filename)
        self._page_label.setStyleSheet(f"""
            color: {COLORS.accent_green};
            font-family: {FONTS.body};
            font-size: {FONTS.size_sm}px;
            font-weight: 600;
        """)
        self._page_spin.setMaximum(self.pdf.page_count)
        self._page_spin.setValue(1)
        self._current_page = 0

        self._toc_list.clear()
        toc = self.pdf.get_toc()
        self._populate_toc(toc)

        self._load_page(0)
        self.status_message.emit(f"已加载: {filename} // {self.pdf.page_count} 页")

    def _populate_toc(self, items, depth=0):
        for item in items:
            prefix = "  " * depth
            marker = "▸" if depth == 0 else "▹"
            list_item = QListWidgetItem(f"{prefix}{marker} {item['title']}")
            list_item.setData(Qt.ItemDataRole.UserRole, item["page"])
            self._toc_list.addItem(list_item)
            if item.get("children"):
                self._populate_toc(item["children"], depth + 1)

    def _toc_clicked(self, item):
        page = item.data(Qt.ItemDataRole.UserRole)
        if page:
            self._page_spin.setValue(page)

    def _load_page(self, page_num):
        if not self.pdf.doc:
            return
        self._current_page = page_num
        text = self.pdf.get_page_text(page_num)
        self._pdf_text.setPlainText(text)

        # Render page image
        from PyQt5.QtGui import QPixmap
        img_bytes = self.pdf.get_page_image(page_num, dpi=150)
        if img_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)

            # Full image tab (full DPI, scrollable)
            self._page_image_label.setPixmap(pixmap)
            self._page_image_label.setFixedSize(pixmap.size())

            # Side-by-side: scale to fit panel width (~550px)
            side_scaled = pixmap.scaledToWidth(550, Qt.TransformationMode.SmoothTransformation)
            self._side_image_label.setPixmap(side_scaled)
            self._side_image_label.setFixedSize(side_scaled.size())

            # Side-by-side: right text
            self._side_text.setPlainText(text)

            # Store original for rescaling on resize
            self._side_full_pixmap = pixmap
        else:
            self._page_image_label.setText("无法渲染此页")

    def _goto_page(self, page):
        self._load_page(page - 1)

    def _prev_page(self):
        if self._current_page > 0:
            self._page_spin.setValue(self._current_page)

    def _next_page(self):
        if self._current_page < self.pdf.page_count - 1:
            self._page_spin.setValue(self._current_page + 2)

    def _pdf_context_menu(self, pos):
        """Right-click context menu for PDF text area."""
        selected = self._pdf_text.textCursor().selectedText().strip()
        menu = QMenu(self)
        if selected:
            translate_action = QAction("翻译选中文本", self)
            translate_action.triggered.connect(lambda: self._translate_pdf_selection(selected))
            menu.addAction(translate_action)
        copy_action = QAction("复制全部", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(
            self._pdf_text.toPlainText()))
        menu.addAction(copy_action)
        menu.exec_(self._pdf_text.mapToGlobal(pos))

    def keyPressEvent(self, event):
        """Keyboard shortcuts for PDF navigation and search."""
        if self._mode_tabs.currentIndex() == 1:  # PDF tab active
            if event.key() == Qt.Key.Key_Left:
                self._prev_page()
                return
            if event.key() == Qt.Key.Key_Right:
                self._next_page()
                return
            if event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self._pdf_search_bar.show()
                self._pdf_search_input.setFocus()
                self._pdf_search_input.selectAll()
                return
            if event.key() == Qt.Key.Key_Escape:
                self._cancel_translation()
                self._pdf_search_bar.hide()
                return
        super().keyPressEvent(event)

    def _pdf_search_next(self):
        """Find next occurrence of search text in PDF content."""
        query = self._pdf_search_input.text()
        if not query:
            self._pdf_text.moveCursor(QTextCursor.MoveOperation.Start)
            self._pdf_search_match.setText("")
            return
        found = self._pdf_text.find(query)
        if found:
            self._pdf_search_match.setText("✓")
        else:
            # Wrap around
            self._pdf_text.moveCursor(QTextCursor.MoveOperation.Start)
            found = self._pdf_text.find(query)
            self._pdf_search_match.setText("✓" if found else "未找到")

    def _translate_current_page(self):
        """Translate the entire current PDF page."""
        if not self.pdf.doc:
            return
        text = self.pdf.get_page_text(self._current_page)
        if not text.strip():
            # Try OCR fallback
            if self.ocr.is_available():
                text = self.ocr.get_page_text_with_ocr(self.pdf, self._current_page)
        if not text.strip():
            QMessageBox.information(self, "空白页", "当前页面无可提取文本")
            return
        self._source_edit.setPlainText(text)
        self._mode_tabs.setCurrentIndex(0)
        self._do_translate()

    def _translate_pdf_selection(self, text: str):
        """Send selected PDF text to the translation tab for translation."""
        self._source_edit.setPlainText(text)
        self._mode_tabs.setCurrentIndex(0)
        self._do_translate()

    def _ocr_current_page(self):
        if not self.pdf.doc:
            return
        if not self.ocr.is_available():
            QMessageBox.warning(
                self, "OCR 错误",
                "未安装 Tesseract OCR。\n安装命令: sudo apt install tesseract-ocr"
            )
            return

        progress = QProgressDialog("正在扫描页面...", "取消", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        text = self.ocr.get_page_text_with_ocr(self.pdf, self._current_page)
        progress.close()
        self._pdf_text.setPlainText(text)
        self.status_message.emit(f"OCR 完成 // 第 {self._current_page + 1} 页")

    def _do_translate(self):
        text = self._source_edit.toPlainText().strip()
        if not text:
            return

        engine = self._engine_combo.currentText()
        source_lang = self._get_lang_code(self._source_lang)
        target_lang = self._get_lang_code(self._target_lang)

        self._float_btn.setVisible(False)
        self._cancel_btn.setVisible(True)
        self._cancel_btn.setEnabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status_message.emit(f"正在通过 {engine} 翻译...")

        self._worker = TranslationWorker(
            self.translator, text, engine,
            self.cache if self.config.get("cache_enabled") else None,
            source_lang, target_lang,
        )
        self._worker.finished.connect(self._on_translate_done)
        self._worker.error.connect(self._on_translate_error)
        self._worker.start()

    def _on_translate_done(self, result):
        self._float_btn.setVisible(True)
        self._cancel_btn.setVisible(False)
        QApplication.restoreOverrideCursor()

        translated = result["translated"]
        original = result["original"]

        # Apply term highlighting
        if self.config.get("terminology_highlight", True):
            html = self._highlighter.highlight(translated, self.terminology)
            self._result_edit.setHtml(html)
        else:
            self._result_edit.setPlainText(translated)

        # Show applied terms
        terms = result.get("terms_applied", [])
        if terms:
            terms_str = " | ".join(f"{en}→{zh}" for en, zh in terms[:8])
            if len(terms) > 8:
                terms_str += f" [+{len(terms) - 8}]"
            self._terms_label.setText(f"术语: {terms_str}")
        else:
            self._terms_label.setText("")

        # Populate sentence pair table if parallel view is active
        if self._toggle_pair_btn.isChecked():
            from gui.widgets.sentence_pair_table import split_sentences
            sources = split_sentences(original)
            translations = split_sentences(translated)
            self._pair_table.set_pairs(sources, translations)
            self._pair_table.animate_rows_in(delay_ms=40)

        cache_info = " [缓存]" if result.get("from_cache") else ""
        self.status_message.emit(f"翻译完成 // {result['engine']}{cache_info}")

        # Emit for history auto-save
        self.translation_done.emit(result["original"], translated, result["engine"])

        # Flash green border to signal completion
        self._flash_result_border()

    def _on_translate_error(self, error):
        import sys
        self._float_btn.setVisible(True)
        self._cancel_btn.setVisible(False)
        QApplication.restoreOverrideCursor()
        print(f"[Translation ERROR] {error}", file=sys.stderr)
        self.status_message.emit(f"错误: {error}")
        QMessageBox.warning(self, "翻译错误", error)

    def _is_cjk(self, ch: str) -> bool:
        """Check if a character is Chinese/Japanese/Korean."""
        cp = ord(ch)
        return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
                0x20000 <= cp <= 0x2A6DF or 0xF900 <= cp <= 0xFAFF or
                0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF or  # Kana
                0xAC00 <= cp <= 0xD7AF)  # Hangul

    def _segment_text(self, text: str) -> list[tuple[bool, str]]:
        """Split text into (is_cjk, substring) alternating runs."""
        if not text:
            return []
        segments = []
        current = text[0]
        current_is_cjk = self._is_cjk(text[0])
        for ch in text[1:]:
            ch_is_cjk = self._is_cjk(ch)
            # Treat spaces/punctuation as belonging to previous segment
            if ch_is_cjk == current_is_cjk or ch.isspace() or ch in '.,;:!?()[]{}<>':
                current += ch
            else:
                segments.append((current_is_cjk, current))
                current = ch
                current_is_cjk = ch_is_cjk
        segments.append((current_is_cjk, current))
        return segments

    def _overlay_translate(self):
        """Translate only English segments, preserve Chinese text in place."""
        if not self.pdf.doc:
            return

        # Cancel any running overlay worker before starting a new one
        if hasattr(self, '_overlay_worker') and self._overlay_worker and self._overlay_worker.isRunning():
            self._overlay_worker.requestInterruption()
            self._overlay_worker.wait(500)

        page_num = self._current_page
        blocks = self.pdf.get_page_text_blocks(page_num)
        valid_blocks = [b for b in blocks if b["text"].strip()]
        if not valid_blocks:
            QMessageBox.information(self, "提示", "当前页面无可提取的文本块")
            return

        # Segment each block, merge consecutive EN segments, collect
        block_segments = []   # list of [(is_cjk, text)] with merged EN runs
        en_texts = []         # flat list of English strings in order
        for b in valid_blocks:
            segs = self._segment_text(b["text"].strip())
            # Merge consecutive EN segments for better translation quality
            merged = []
            i = 0
            while i < len(segs):
                is_cjk, text = segs[i]
                if is_cjk or not text.strip():
                    merged.append((is_cjk, text))
                    i += 1
                else:
                    parts = [text.strip()]
                    i += 1
                    while i < len(segs):
                        n_cjk, n_text = segs[i]
                        if n_cjk or not n_text.strip():
                            break
                        parts.append(n_text.strip())
                        i += 1
                    merged.append((False, " ".join(parts)))
            block_segments.append(merged)
            for is_cjk, s in merged:
                if not is_cjk and s.strip():
                    en_texts.append(s.strip())

        if not en_texts:
            QMessageBox.information(self, "提示", "当前页面无可翻译的英文文本")
            return

        # Store state for concurrent translation
        self._overlay_cancelled = False
        self._overlay_blocks = blocks
        self._overlay_valid = valid_blocks
        self._overlay_block_segments = block_segments
        self._overlay_page = page_num
        self._overlay_en_texts = en_texts
        self._overlay_total = len(en_texts)
        self._overlay_translations = [None] * self._overlay_total
        self._overlay_pending = self._overlay_total
        self._overlay_active = 0
        self._overlay_workers = []  # track all active workers for cancellation
        # Extract spans for heading detection and font sizing
        self._overlay_spans = self.pdf.get_page_spans(page_num)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status_message.emit(
            f"原位翻译中... (0/{self._overlay_total})"
        )
        # Launch initial batch of concurrent workers (staggered to avoid TLS contention)
        concurrent = min(3, self._overlay_total)
        for i in range(concurrent):
            QTimer.singleShot(i * 150, self._start_overlay_worker)

    def _start_overlay_worker(self):
        """Start a worker for the next untranslated segment, if any."""
        if self._overlay_cancelled:
            self._check_overlay_done()
            return
        # Find next untranslated index
        try:
            idx = self._overlay_translations.index(None)
        except ValueError:
            return  # all done or all in-flight

        text = self._overlay_en_texts[idx]
        engine = self._engine_combo.currentText()
        src = self._get_lang_code(self._source_lang)
        tgt = self._get_lang_code(self._target_lang)

        worker = TranslationWorker(
            self.translator, text, engine,
            self.cache if self.config.get("cache_enabled") else None,
            src, tgt,
        )
        worker._idx = idx
        worker.finished.connect(self._on_segment_translated)
        worker.error.connect(self._on_segment_error)
        self._overlay_workers.append(worker)
        self._overlay_active += 1
        worker.start()

    def _on_segment_translated(self, result):
        worker = self.sender()
        idx = worker._idx
        # Guard against stale workers from a cancelled previous run
        if idx >= len(self._overlay_translations):
            return
        self._overlay_translations[idx] = result["translated"]
        self._overlay_active -= 1
        self._overlay_pending -= 1
        done = self._overlay_total - self._overlay_pending
        self.status_message.emit(
            f"原位翻译中... ({done}/{self._overlay_total})"
        )
        worker.wait()
        self._overlay_workers.remove(worker)
        if not self._overlay_cancelled:
            self._start_overlay_worker()
        self._check_overlay_done()

    def _on_segment_error(self, error):
        worker = self.sender()
        idx = worker._idx
        # Guard against stale workers from a cancelled previous run
        if idx >= len(self._overlay_translations):
            return
        self._overlay_translations[idx] = self._overlay_en_texts[idx]
        self._overlay_active -= 1
        self._overlay_pending -= 1
        done = self._overlay_total - self._overlay_pending
        self.status_message.emit(
            f"原位翻译中... ({done}/{self._overlay_total}) [1 段失败]"
        )
        worker.wait()
        self._overlay_workers.remove(worker)
        if not self._overlay_cancelled:
            self._start_overlay_worker()
        self._check_overlay_done()

    def _check_overlay_done(self):
        """Check if all overlay workers have finished, then finalize or cancel."""
        if self._overlay_active > 0:
            return
        if self._overlay_cancelled:
            QApplication.restoreOverrideCursor()
            self.status_message.emit("原位翻译已取消")
        else:
            self._finish_overlay()

    def _finish_overlay(self):
        """Paint overlay via QPainter: recombine translated EN with preserved CJK.

        Uses QPainter bitmap overlay instead of PyMuPDF redactions because
        PyMuPDF's apply_redactions() internally re-inserts fonts without
        preserving the fontbuffer, which breaks CJK font rendering.
        """
        from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen

        # Recombine each block: swap English segments with translations
        trans_map = {}
        en_idx = 0
        for bi, segs in enumerate(self._overlay_block_segments):
            recombined = []
            for is_cjk, text in segs:
                if is_cjk or not text.strip():
                    recombined.append(text)
                else:
                    if en_idx < len(self._overlay_translations):
                        recombined.append(self._overlay_translations[en_idx])
                    else:
                        recombined.append(text)
                    en_idx += 1
            block_no = self._overlay_valid[bi]["block_no"]
            trans_map[block_no] = "".join(recombined)

        # --- Body font size: median of all span sizes on the page ---
        all_sizes = sorted(
            s["font_size"] for s in self._overlay_spans if s["font_size"] > 0
        )
        body_fs = all_sizes[len(all_sizes) // 2] if all_sizes else 10

        dpi = 150
        scale = dpi / 72.0
        img_bytes = self.pdf.get_page_image(self._overlay_page, dpi=dpi)
        if not img_bytes:
            QApplication.restoreOverrideCursor()
            self.status_message.emit("无法渲染页面")
            return

        # -- Left: original page image ----------------------------------
        orig = QPixmap()
        orig.loadFromData(img_bytes)
        self._overlay_orig_label.setPixmap(orig)
        self._overlay_orig_label.setFixedSize(orig.size())

        # -- Right: painted overlay -------------------------------------
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)
        pm_h = pixmap.height()

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        translated_count = 0
        for b in self._overlay_blocks:
            block_no = b["block_no"]
            if block_no not in trans_map:
                continue
            translated = trans_map[block_no]
            if not translated.strip():
                continue

            x0, y0, x1, y1 = b["bbox"]
            rx = int(x0 * scale)
            ry = int(y0 * scale)
            rw = int((x1 - x0) * scale)
            rh = int((y1 - y0) * scale)
            rx = max(0, rx); ry = max(0, ry)
            rw = min(rw, pixmap.width() - rx)
            rh = min(rh, pm_h - ry)
            if rw < 15 or rh < 6:
                continue

            painter.fillRect(rx, ry, rw, rh, QColor(22, 22, 22, 235))

            # Start with block's own font size, scaled to DPI
            # CJK chars need ~15% more height at same point size; start smaller
            block_fs = b.get("font_size", body_fs)
            font_size = int(block_fs * scale * 0.72)
            font_size = max(6, min(font_size, int(rh * 0.55)))

            # Iterative shrink: set font, measure, reduce, repeat until text fits
            for _ in range(5):
                font = QFont("WenQuanYi Micro Hei", font_size)
                painter.setFont(font)
                text_rect = painter.boundingRect(rx + 3, ry + 2, rw - 6, rh - 4,
                                                 Qt.TextFlag.TextWordWrap, translated)
                if text_rect.height() <= rh - 4:
                    break
                ratio = min((rh - 4) / max(text_rect.height(), 1),
                           (rw - 6) / max(text_rect.width(), 1))
                font_size = max(6, int(font_size * ratio * 0.92))

            painter.setPen(QPen(QColor("#e8e8e8")))
            painter.drawText(rx + 3, ry + 2, rw - 6, rh - 4,
                            Qt.TextFlag.TextWordWrap, translated)
            translated_count += 1

        painter.end()
        self._overlay_label.setPixmap(pixmap)
        self._overlay_label.setFixedSize(pixmap.size())
        self._mode_tabs.setCurrentIndex(1)
        self._pdf_tabs.setCurrentIndex(4)
        QApplication.restoreOverrideCursor()
        self.status_message.emit(f"原位翻译完成 · {translated_count} 个文本块")

    def _cancel_translation(self):
        """Cancel any running translation (panel or overlay)."""
        cancelled = False
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(500)
            cancelled = True
        if hasattr(self, '_overlay_workers'):
            for w in self._overlay_workers:
                if w.isRunning():
                    w.requestInterruption()
            self._overlay_cancelled = True
            cancelled = True
        if cancelled:
            QApplication.restoreOverrideCursor()
            self.status_message.emit("正在取消...")

    def _flash_result_border(self):
        """Briefly flash the result area border green to signal completion."""
        c = COLORS
        self._result_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 2px solid {c.accent_green};
                border-left: 3px solid {c.accent_green};
                border-radius: 10px;
                padding: 16px;
                font-family: 'SF Pro Text', 'Noto Sans SC', sans-serif;
                font-size: 17px;
                line-height: 1.8;
                selection-background-color: {c.accent_green}30;
            }}
        """)
        QTimer.singleShot(400, self._restore_result_border)

    def _restore_result_border(self):
        """Restore normal result border after flash."""
        c = COLORS
        self._result_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-left: 3px solid {c.accent_green}40;
                border-radius: 10px;
                padding: 16px;
                font-family: 'SF Pro Text', 'Noto Sans SC', sans-serif;
                font-size: 17px;
                line-height: 1.8;
                selection-background-color: {c.accent_green}30;
            }}
        """)

    def on_hotkey_translate(self, text: str):
        """Handle hotkey-triggered translation."""
        if not text:
            self.status_message.emit("未选中文本")
            return
        self._source_edit.setPlainText(text)
        self._do_translate()

    def reapply_theme(self):
        """Reapply styles after theme switch without losing state."""
        from gui.theme import (
            COLORS as c, FONTS, TEXT_EDIT_STYLE, LIST_WIDGET_STYLE,
            COMBO_BOX_STYLE, PUSH_BUTTON_STYLE, TAB_WIDGET_STYLE,
            SPLITTER_STYLE, SPIN_BOX_STYLE,
        )
        self._mode_tabs.setStyleSheet(TAB_WIDGET_STYLE)
        self._source_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._target_lang.setStyleSheet(COMBO_BOX_STYLE)
        self._engine_combo.setStyleSheet(COMBO_BOX_STYLE)
        self._toggle_pair_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        self._source_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_input};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-left: 3px solid {c.accent_blue}40;
                border-radius: 10px;
                padding: 12px;
                font-family: 'SF Pro Text', sans-serif;
                font-size: {FONTS.size_md}px;
                selection-background-color: {c.accent_blue}40;
            }}
            QTextEdit:focus {{ border-color: {c.accent_blue}; border-left-color: {c.accent_blue}; }}
        """)
        self._result_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-left: 3px solid {c.accent_green}40;
                border-radius: 10px;
                padding: 16px;
                font-family: 'SF Pro Text', 'Noto Sans SC', sans-serif;
                font-size: 17px;
                line-height: 1.8;
                selection-background-color: {c.accent_green}30;
            }}
            QTextEdit:focus {{
                border-color: {c.accent_green};
                border-left-color: {c.accent_green};
            }}
        """)
        self._float_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        self._cancel_btn.setStyleSheet(PUSH_BUTTON_STYLE)
        self._page_spin.setStyleSheet(SPIN_BOX_STYLE)
        self._toc_list.setStyleSheet(f"""
            QListWidget {{
                background: {c.bg_input};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 10px;
                padding: 6px;
                font-family: {FONTS.body};
                font-size: {FONTS.size_sm}px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 8px;
                margin: 2px 0;
                border-left: 3px solid transparent;
            }}
            QListWidget::item:hover {{
                background: {c.bg_hover};
                border-left-color: {c.accent_blue};
            }}
            QListWidget::item:selected {{
                background: {c.bg_active};
                color: {c.text_bright};
                border-left-color: {c.accent_blue};
            }}
        """)
        self._pdf_text.setStyleSheet(f"""
            QTextEdit {{
                background: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 10px;
                padding: 16px;
                font-family: 'SF Pro Text', 'Noto Sans SC', sans-serif;
                font-size: 14px;
                line-height: 1.7;
                selection-background-color: {c.accent_blue}40;
            }}
        """)
        self._pair_table.reapply_theme()
        self._highlighter.accent_green = c.accent_green
        self._highlighter.text_primary = c.text_primary

    # -- Drag & drop PDF --------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self._load_pdf(path)
                break
