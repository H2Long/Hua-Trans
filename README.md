# 黄花梨之译 (Hua-Trans)

面向电子信息专业人员的 PDF 数据手册翻译工具。选中文本一键翻译，PDF 原位覆译，318 个内置 EE 专业术语。

## 功能

- **热键翻译**：任意应用选中英文文本 → `Ctrl+Shift+T` → 鼠标旁弹出译文
- **PDF 原位翻译**：打开 PDF 数据手册 → 点击「原位翻译」→ 英文块替换为中文（左原图/右译文对照）
- **多翻译引擎**：Google（免费）、DeepL、Claude/GPT（需 API Key）
- **EE 术语库**：318 条内置电子工程术语，支持自定义增删导入导出
- **PDF 工具集**：文本提取、目录解析、OCR 扫描件、页面搜索、拖拽打开
- **翻译缓存**：SQLite 本地缓存，重复文本秒出结果

## 系统要求

- **操作系统**：Linux（X11）
- **Python**：3.10+
- **依赖包**：PyQt5, PyMuPDF, pynput, pyperclip, Pillow, requests
- **可选**：Tesseract OCR（扫描件 OCR 需要）

## 快速安装

### 方式一：一键脚本

```bash
curl -fsSL https://raw.githubusercontent.com/H2Long/Hua-Trans/main/install.sh | bash
```

### 方式二：手动安装

```bash
# 克隆仓库
git clone git@github.com:H2Long/Hua-Trans.git
cd Hua-Trans

# 安装依赖
pip install -r requirements.txt

# 安装中文字体（原位翻译覆绘需要）
sudo apt install fonts-wqy-microhei

# 可选：安装 OCR 支持
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim
```

## 使用

### 启动

```bash
# 开发模式
python main.py

# 热键功能需要 sudo（pynput 全局热键监听）
sudo python main.py
```

### 热键翻译

1. 在任意应用中选中英文文本
2. 按 `Ctrl+Shift+T`
3. 译文在鼠标附近弹出

悬浮窗操作：
- 下拉框切换翻译引擎
- `◀` `▶` 浏览本次会话翻译历史
- `⊡` 切换紧凑/完整模式
- `📋` 复制译文到剪贴板

### PDF 翻译

1. 点击工具栏「打开 PDF」或拖拽 PDF 到窗口
2. 左侧目录，右侧文本内容
3. 在「PDF 阅读」标签页中浏览

**原位翻译**：
1. 打开 PDF 数据手册，定位到需要翻译的页面
2. 点击「原位翻译」按钮
3. 左面板显示原页面，右面板显示译文覆绘

**面板翻译**：
1. 切换到「翻译」标签
2. 粘贴或从 PDF 选中文本后右键「翻译选中文本」
3. 点击「翻译」或 `Ctrl+Return`

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Shift+T` | 全局热键翻译 |
| `Ctrl+Return` | 翻译面板提交 |
| `Ctrl+1` ~ `Ctrl+4` | 切换页面标签 |
| `←` `→` | PDF 翻页 |
| `Ctrl+F` | PDF 页面搜索 |

## 配置

配置文件：`~/.translatetor/config.json`

```json
{
  "hotkey": "ctrl+shift+t",
  "translation_engine": "google",
  "source_lang": "en",
  "target_lang": "zh",
  "theme": "deep_purple_blue",
  "font_size": 14,
  "popup_width": 450,
  "popup_opacity": 0.95,
  "auto_hide_seconds": 0,
  "cache_enabled": true,
  "cache_max_days": 30,
  "terminology_highlight": true
}
```

### 翻译引擎

| 引擎 | 说明 |
|------|------|
| `google` | 免费，无需 API Key，适合大量使用 |
| `deepl` | 需要 DeepL API Key（`deepl_api_key`） |
| `llm` | 兼容 Anthropic / OpenAI API（`llm_api_key`, `llm_base_url`, `llm_model`） |

### 主题

- `deep_purple_blue` — 深紫蓝（默认，暗色 Apple 风格）
- `minimal_apple` — 浅色 Apple 风格
- `amber_gold` — 暖金暗色（适合长时间阅读）
- `dark_professional` — VS Code 暗色
- `minimal_white` — 纯白

## 术语库

内置 318 条电子工程专业术语，涵盖：
- 半导体器件（MOSFET, BJT, Schottky, Latch-up...）
- 放大器参数（Phase Margin, CMRR, Slew Rate...）
- 数据转换器（ADC, ENOB, SFDR, DNL...）
- 电源管理（LDO, Buck, PSRR, Soft Start...）
- 时钟时序（Jitter, PLL, Setup Time...）
- 接口通信（SPI, I2C, LVDS, CAN...）
- 存储器（SRAM, EEPROM, Wear Leveling...）
- PCB 封装（Footprint, Via, Impedance...）

### 自定义术语

1. 切换到「术语」标签页
2. 点击「添加术语」
3. 输入英文和中文翻译
4. 支持导入/导出 JSON 文件

术语文件：`~/.translatetor/terms.json`

```json
{
  "New Term": "新术语",
  "Another Term": "另一个术语"
}
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行
python main.py

# 打包为独立可执行文件
pip install pyinstaller
python build.py
# 输出: dist/黄花梨之译

# 安装到系统
sudo ./install.sh
```

## 项目结构

```
main.py                 # 入口
core/                   # 业务逻辑
  config.py             # 配置管理
  translator.py         # 翻译引擎（Google/DeepL/LLM）
  terminology.py        # EE 术语库
  cache.py              # SQLite 翻译缓存
  clipboard.py          # 剪贴板管理（X11 PRIMARY 选区）
  pdf_handler.py        # PDF 文本提取/渲染
  ocr_handler.py        # Tesseract OCR
  hotkey_manager.py     # 运行时热键管理
gui/                    # PyQt5 界面
  main_window.py        # 主窗口 + 侧栏导航
  floating_widget.py    # 悬浮翻译窗
  sidebar.py            # 玻璃质感侧栏
  theme.py              # 主题系统（5 套配色）
  pages/                # 4 个页面标签
  widgets/              # 可复用控件
```

## 常见问题

### 热键不生效

- 确保用 `sudo` 启动（pynput 需要 root 权限监听全局键盘事件）
- 检查快捷键是否与其他程序冲突

### OCR 不可用

- 安装 tesseract：`sudo apt install tesseract-ocr tesseract-ocr-eng`

### 原位翻译中文显示不全

- 安装中文字体：`sudo apt install fonts-wqy-microhei`

### 翻译引擎报错

- Google：检查网络连接，Google Translate API 可能需要代理
- DeepL：确认 API Key 正确，免费版使用 `https://api-free.deepl.com`
- LLM：确认 `llm_base_url` 和 `llm_model` 与你的 API 提供商匹配

## 许可证

MIT License
