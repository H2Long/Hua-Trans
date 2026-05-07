#!/usr/bin/env bash
# 黄花梨之译 (Hua-Trans) — 卸载脚本
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${RED}[✗]${NC} $*"; }

echo "卸载 黄花梨之译 (Hua-Trans)..."

# 移除桌面启动器
DESKTOP_FILE="$HOME/.local/share/applications/hua-trans.desktop"
if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    log "桌面启动器已移除"
fi

# 移除启动命令
WRAPPER="$HOME/.local/bin/hua-trans"
if [ -f "$WRAPPER" ]; then
    rm -f "$WRAPPER"
    log "启动命令已移除 (hua-trans)"
fi

# 清理 bashrc
if [ -f "$HOME/.bashrc" ]; then
    sed -i '/# 黄花梨之译/d' "$HOME/.bashrc" 2>/dev/null || true
    sed -i '/hua-trans/d' "$HOME/.bashrc" 2>/dev/null || true
    log "终端配置已清理"
fi

# 询问是否删除配置和数据
CONFIG_DIR="$HOME/.translatetor"
if [ -d "$CONFIG_DIR" ]; then
    echo ""
    read -rp "是否删除所有配置和翻译缓存？($CONFIG_DIR) [y/N] " answer
    if [ "${answer,,}" = "y" ] || [ "${answer,,}" = "yes" ]; then
        rm -rf "$CONFIG_DIR"
        log "配置和缓存已删除"
    else
        echo "保留: $CONFIG_DIR"
    fi
fi

echo ""
echo -e "${GREEN}卸载完成。${NC}"
