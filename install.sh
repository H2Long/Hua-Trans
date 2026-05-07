#!/usr/bin/env bash
# 黄花梨之译 (Hua-Trans) — 一键安装脚本
# 用法: curl -fsSL <url> | bash  或  ./install.sh
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; exit 1; }
info() { echo -e "${CYAN}[i]${NC} $*"; }

echo -e "${CYAN}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║       黄花梨之译 Hua-Trans          ║"
echo "  ║   电子工程数据手册 PDF 翻译工具       ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── 权限检查 ──
if [ "$EUID" -eq 0 ]; then
    warn "检测到 root 权限。Hua-Trans 使用 XGrabKey，普通用户即可使用热键。"
fi

# ── 系统依赖 ──
info "检查系统依赖..."

MISSING=""
command -v python3 >/dev/null 2>&1 || MISSING="$MISSING python3"
command -v pip3 >/dev/null 2>&1 || MISSING="$MISSING pip3"

if [ -n "$MISSING" ]; then
    err "缺少必要依赖:$MISSING。请先安装: sudo apt install python3 python3-pip python3-venv"
fi

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$(echo "$PYTHON_VER < 3.10" | bc -l 2>/dev/null || echo 1)" = "1" ]; then
    warn "Python 版本: $PYTHON_VER（建议 3.10+）"
fi

log "Python $PYTHON_VER"

# ── 项目目录 ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/main.py" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
    info "检测到本地仓库: $PROJECT_DIR"
else
    PROJECT_DIR="$HOME/.local/share/hua-trans"
    info "克隆到: $PROJECT_DIR"
    if [ -d "$PROJECT_DIR" ]; then
        warn "目录已存在，正在更新..."
        cd "$PROJECT_DIR"
        git pull --ff-only 2>/dev/null || warn "git pull 失败，使用现有版本"
    else
        mkdir -p "$(dirname "$PROJECT_DIR")"
        git clone https://github.com/H2Long/Hua-Trans.git "$PROJECT_DIR" 2>/dev/null || \
            err "克隆失败。请检查网络或手动下载: git clone https://github.com/H2Long/Hua-Trans.git"
    fi
fi

cd "$PROJECT_DIR"

# ── Python 依赖 ──
info "安装 Python 依赖..."
pip3 install --user -r requirements.txt 2>/dev/null || \
    pip3 install -r requirements.txt --break-system-packages 2>/dev/null || \
    err "依赖安装失败。请手动执行: pip install -r requirements.txt"

log "Python 依赖安装完成"

# ── CJK 字体 ──
info "检查中文字体..."
if fc-list | grep -qi "wqy.*micro\|wenquanyi.*micro"; then
    log "文泉驿微米黑已安装"
else
    warn "未检测到 wqy-microhei 字体"
    if command -v apt-get >/dev/null 2>&1; then
        info "尝试安装 fonts-wqy-microhei..."
        if [ "$EUID" -eq 0 ]; then
            apt-get update -qq && apt-get install -y -qq fonts-wqy-microhei && log "字体安装完成"
        else
            warn "需要 root 权限安装字体: sudo apt install fonts-wqy-microhei"
            warn "也可跳过字体安装，原位翻译覆绘使用系统默认字体"
        fi
    fi
fi

# ── 可选: OCR ──
if command -v tesseract >/dev/null 2>&1; then
    log "Tesseract OCR 已安装"
else
    warn "Tesseract OCR 未安装（扫描件 PDF 需要）"
    info "安装命令: sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim"
fi

# ── 桌面入口 ──
DESKTOP_FILE="$HOME/.local/share/applications/hua-trans.desktop"
if [ ! -f "$DESKTOP_FILE" ]; then
    info "创建桌面启动器..."
    mkdir -p "$HOME/.local/share/applications"
    cat > "$DESKTOP_FILE" << DESKTOPEOF
[Desktop Entry]
Name=黄花梨之译
Name[en]=Hua-Trans
Comment=电子工程数据手册 PDF 翻译工具
Comment[en]=EE Datasheet PDF Translation Tool
Exec=$HOME/.local/bin/hua-trans
Icon=$PROJECT_DIR/resources/icon.png
Terminal=false
Type=Application
Categories=Development;Education;Engineering;
Keywords=translate;datasheet;electronics;engineering;翻译;数据手册;PDF;
DESKTOPEOF
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    log "桌面启动器已创建"
else
    info "桌面启动器已存在，跳过"
fi

# ── 创建启动命令 ──
BIN_DIR="$HOME/.local/bin"
WRAPPER="$BIN_DIR/hua-trans"
mkdir -p "$BIN_DIR"
cp "$PROJECT_DIR/hua-trans" "$WRAPPER"
log "启动命令已安装: hua-trans"

# Ensure ~/.local/bin is in PATH
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    if ! grep -q "$BIN_DIR" "$HOME/.bashrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        log "~/.local/bin 已添加到 PATH（重新打开终端生效）"
    fi
fi

# ── 完成 ──
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       安装完成！                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo "  启动方式："
echo "    1. 应用菜单搜索「黄花梨之译」"
echo "    2. 终端: hua-trans"
echo "    3. 手动: cd $PROJECT_DIR && python3 main.py"
echo ""
echo "  热键无需 root 权限（使用 X11 XGrabKey）"
echo ""
echo "  配置: ~/.translatetor/config.json"
echo "  术语: ~/.translatetor/terms.json"
echo "  缓存: ~/.translatetor/cache/"
echo ""
echo -e "  ${CYAN}重新加载终端别名: source ~/.bashrc${NC}"
echo ""
