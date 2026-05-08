# 黄花梨之译 (Hua-Trans) — Windows 一键安装脚本
# 用法: 右键 PowerShell → 以管理员身份运行此脚本
#   或: iwr -Uri "https://raw.githubusercontent.com/H2Long/Hua-Trans/main/install.ps1" | iex

param(
    [switch]$NoOcr = $false
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "黄花梨之译 安装程序"

# ── 颜色输出 ──
function Write-Success { Write-Host "[✓] $args" -ForegroundColor Green }
function Write-Warn    { Write-Host "[!] $args" -ForegroundColor Yellow }
function Write-ErrorMsg { Write-Host "[✗] $args" -ForegroundColor Red }
function Write-Info    { Write-Host "[i] $args" -ForegroundColor Cyan }

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║       黄花梨之译 Hua-Trans           ║" -ForegroundColor Cyan
Write-Host "  ║   电子工程数据手册 PDF 翻译工具       ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Python 检查 ──
Write-Info "检查 Python..."

$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $v = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $v -match "3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 10) {
                $pythonCmd = $cmd
                break
            }
        }
    } catch { }
}

if (-not $pythonCmd) {
    Write-ErrorMsg "未找到 Python 3.10+。请从 https://www.python.org/downloads/ 安装。"
    Write-Info "安装时务必勾选 'Add Python to PATH'"
    exit 1
}

Write-Success "Python $(& $pythonCmd --version)"

# ── 项目目录 ──
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path "$scriptPath\main.py") {
    $projectDir = $scriptPath
    Write-Info "检测到本地仓库: $projectDir"
} else {
    $projectDir = "$env:LOCALAPPDATA\hua-trans"
    Write-Info "安装到: $projectDir"

    if (Test-Path $projectDir) {
        Write-Warn "目录已存在，正在更新..."
        try {
            Push-Location $projectDir
            git pull --ff-only 2>$null
            Pop-Location
        } catch {
            Write-Warn "git pull 失败，使用现有版本"
        }
    } else {
        Write-Info "克隆仓库..."
        New-Item -ItemType Directory -Force -Path (Split-Path $projectDir) | Out-Null
        git clone https://github.com/H2Long/Hua-Trans.git $projectDir 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMsg "克隆失败。请检查网络或手动下载。"
            exit 1
        }
    }
}

Push-Location $projectDir

# ── Python 依赖 ──
Write-Info "安装 Python 依赖..."
& $pythonCmd -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "依赖安装失败。请手动执行: pip install -r requirements.txt"
    Pop-Location
    exit 1
}
Write-Success "Python 依赖安装完成"

# ── 可选: Tesseract OCR ──
if (-not $NoOcr) {
    $tesseractPath = Get-Command tesseract -ErrorAction SilentlyContinue
    if ($tesseractPath) {
        Write-Success "Tesseract OCR 已安装"
    } else {
        Write-Warn "Tesseract OCR 未安装（扫描件 PDF 需要）"
        Write-Info "下载地址: https://github.com/UB-Mannheim/tesseract/wiki"
        Write-Info "安装时请勾选中文语言包 (Chinese Simplified)"
    }
}

# ── 创建启动脚本 ──
$binDir = "$env:LOCALAPPDATA\hua-trans"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

# 复制 hua-trans launcher 到 bin 目录
if (Test-Path "$projectDir\hua-trans") {
    Copy-Item "$projectDir\hua-trans" "$binDir\hua-trans.py" -Force
}

# 创建批处理启动器
$launcherPath = "$binDir\hua-trans.bat"
@"
@echo off
pushd "$projectDir"
"$pythonCmd" main.py %*
popd
"@ | Out-File -FilePath $launcherPath -Encoding ASCII

Write-Success "启动命令已安装: $launcherPath"

# ── 开始菜单快捷方式 ──
$startMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\黄花梨之译"
New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null

$WScriptShell = New-Object -ComObject WScript.Shell

# 主程序快捷方式
$shortcutPath = "$startMenuDir\黄花梨之译.lnk"
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcherPath
$shortcut.WorkingDirectory = $projectDir
if (Test-Path "$projectDir\resources\icon.png") {
    $shortcut.IconLocation = "$projectDir\resources\icon.png"
}
$shortcut.Description = "电子工程数据手册 PDF 翻译工具"
$shortcut.Save()

# 卸载快捷方式
$uninstallShortcut = $WScriptShell.CreateShortcut("$startMenuDir\卸载黄花梨之译.lnk")
$uninstallShortcut.TargetPath = "powershell.exe"
$uninstallShortcut.Arguments = "-Command `"Remove-Item -Recurse -Force '$startMenuDir'; Remove-Item -Recurse -Force '$projectDir'; Write-Host '黄花梨之译已卸载' -ForegroundColor Green; Read-Host '按 Enter 退出'`""
$uninstallShortcut.Save()

Write-Success "开始菜单快捷方式已创建"

# ── PATH 检查 ──
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
    Write-Info "$binDir 已添加到用户 PATH（新终端生效）"
}

# ── 完成 ──
Pop-Location

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║       安装完成！                     ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  启动方式："
Write-Host "    1. 开始菜单 → 黄花梨之译"
Write-Host "    2. 终端: hua-trans"
Write-Host "    3. 手动: cd $projectDir && $pythonCmd main.py"
Write-Host ""
Write-Host "  热键: Ctrl+Shift+T（选中文本即可翻译）"
Write-Host "  托盘: 关闭窗口后最小化到系统托盘"
Write-Host ""
Write-Host "  配置: ~/.translatetor/config.json"
Write-Host "  术语: ~/.translatetor/terms.json"
Write-Host "  缓存: ~/.translatetor/cache/"
Write-Host ""
Write-Host "  首次启动如有防火墙弹窗，请允许 Python 联网。" -ForegroundColor Yellow
Write-Host ""
