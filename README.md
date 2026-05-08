# 黄花梨之译 (Hua-Trans)

面向电子信息专业人员的 PDF 数据手册翻译工具。选中文本一键翻译，PDF 原位覆译，356 个内置 EE 专业术语。**支持 Linux / Windows。**

## 功能

- **热键翻译**：任意应用选中英文文本 → `Ctrl+Shift+T` → 鼠标旁弹出译文
- **PDF 原位翻译**：打开 PDF 数据手册 → 点击「原位翻译」→ 英文块替换为中文（左原图/右译文对照）
- **多翻译引擎**：Google（免费）、DeepL、Claude/GPT（需 API Key）
- **EE 术语库**：356 条内置电子工程术语，支持自定义增删导入导出
- **PDF 工具集**：文本提取、目录解析、OCR 扫描件、页面搜索、拖拽打开、Ctrl+滚轮缩放
- **翻译缓存**：SQLite 本地缓存，重复文本秒出结果
- **系统托盘**：关闭窗口最小化到托盘，后台随时待命
- **主题切换**：侧栏一键切换暗色/亮色，5 套主题可选

## 系统要求

| 要求 | Linux | Windows |
|------|-------|---------|
| 操作系统 | X11 (Wayland 需 XWayland) | Windows 10+ |
| Python | 3.10+ | 3.10+ |
| 热键依赖 | python-xlib (XGrabKey) | pynput |
| 中文字体 | fonts-wqy-microhei | Microsoft YaHei (系统自带) |
| 可选 | Tesseract OCR | Tesseract OCR |

## 快速安装

### Linux

```bash
# 一键安装（推荐）
curl -fsSL https://raw.githubusercontent.com/H2Long/Hua-Trans/main/install.sh | bash

# 或手动安装
git clone git@github.com:H2Long/Hua-Trans.git
cd Hua-Trans
pip install -r requirements.txt
sudo apt install fonts-wqy-microhei   # 原位翻译中文字体
```

安装后终端输入 `hua-trans` 启动，或在应用菜单搜索「黄花梨之译」。

### Windows

**方式一：一键安装脚本（推荐）**

在 PowerShell 中运行（右键 → 以管理员身份运行，非必须但推荐）：

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
iwr -Uri "https://raw.githubusercontent.com/H2Long/Hua-Trans/main/install.ps1" -OutFile "$env:TEMP\install.ps1"
& "$env:TEMP\install.ps1"
```

脚本会自动：检测 Python → 安装依赖 → 创建开始菜单快捷方式 → 可选安装 Tesseract OCR。

**方式二：手动安装**

```powershell
# 克隆仓库
git clone https://github.com/H2Long/Hua-Trans.git
cd Hua-Trans

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

### macOS（实验性）

```bash
git clone https://github.com/H2Long/Hua-Trans.git
cd Hua-Trans
pip install -r requirements.txt
python main.py
```

> macOS 热键功能需要 `pynput` 辅助功能权限。手动安装：`pip install pynput`。

## 使用

### 启动

| 平台 | 方式 |
|------|------|
| Linux | 终端 `hua-trans` 或应用菜单「黄花梨之译」 |
| Windows | 开始菜单「黄花梨之译」或终端 `python main.py` |

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

1. 点击工具栏「打开 PDF」或**拖拽 PDF 到窗口**
2. 左侧目录，右侧文本内容
3. 在「PDF 阅读」标签页中浏览
4. `Ctrl+滚轮` 缩放页面，`+` / `−` 按钮调整分辨率

**原位翻译**：
1. 打开 PDF 数据手册，定位到需要翻译的页面
2. 点击「原位翻译」按钮
3. 左面板显示原页面，右面板显示译文覆绘

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Shift+T` | 全局热键翻译（选中文本即可） |
| `Ctrl+Return` | 翻译面板提交 |
| `Ctrl+1` ~ `Ctrl+4` | 切换页面标签 |
| `←` `→` | PDF 翻页 |
| `Ctrl+F` | PDF 页面搜索 |
| `Ctrl+滚轮` | PDF 页面缩放 |

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
| `deepl` | 需要 DeepL API Key（`deepl_api_key`）。免费 Key 以 `:fx` 结尾 |
| `llm` | 兼容 Anthropic / OpenAI API（`llm_api_key`, `llm_base_url`, `llm_model`） |

### 主题

- `deep_purple_blue` — 深紫蓝（默认，暗色 Apple 风格）
- `minimal_apple` — 浅色 Apple 风格
- `amber_gold` — 暖金暗色（适合长时间阅读）
- `dark_professional` — VS Code 暗色
- `minimal_white` — 纯白

**快速切换**：侧栏底部 ☀/☾ 按钮一键切换暗色/亮色。

## 术语库

内置 356 条电子工程专业术语，涵盖：
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
# 安装依赖
pip install -r requirements.txt

# 运行
./hua-trans       # Linux
python main.py    # Windows / macOS

# 打包为独立可执行文件
pip install pyinstaller
python build.py
# 输出: dist/黄花梨之译
```

## 项目结构

```
main.py                 # 入口 + 系统托盘
core/                   # 业务逻辑
  config.py             # 配置管理
  translator.py         # 翻译引擎（Google/DeepL/LLM）
  terminology.py        # EE 术语库
  cache.py              # SQLite 翻译缓存（连接复用）
  clipboard.py          # 剪贴板管理（X11/Win 平台适配）
  pdf_handler.py        # PDF 文本提取/渲染
  ocr_handler.py        # Tesseract OCR
  hotkey_manager.py     # 热键管理（Linux X11 / Win pynput）
  text_utils.py         # CJK 文本分段工具
  usage_tracker.py      # API 用量统计
gui/                    # PyQt5 界面
  main_window.py        # 主窗口 + 侧栏导航
  floating_widget.py    # 悬浮翻译窗
  sidebar.py            # 侧栏 + 主题切换
  theme.py              # 主题系统（5 套配色）
  pages/                # 4 个页面标签
  widgets/              # 可复用控件
```

## 常见问题

### 热键不生效

- **Linux**：确认 `python-xlib` 已安装：`pip install python-xlib`。X11 下无需 root。
- **Windows**：确认 `pynput` 已安装：`pip install pynput`。Firewall 弹窗点允许。
- 检查快捷键是否与其他程序冲突。

### OCR 不可用

- **Linux**：`sudo apt install tesseract-ocr tesseract-ocr-eng`
- **Windows**：安装 [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)，安装时勾选中文语言包

### 原位翻译中文不显示 / 显示乱码

- **Linux**：`sudo apt install fonts-wqy-microhei`
- **Windows**：系统自带 Microsoft YaHei 无需额外安装

### 翻译引擎报错

- Google：检查网络连接，可能需要代理
- DeepL：免费 Key 以 `:fx` 结尾，使用 `https://api-free.deepl.com`
- LLM：确认 `llm_base_url` 和 `llm_model` 与你的 API 提供商匹配

## 许可证

MIT License
