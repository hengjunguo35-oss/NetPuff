#!/bin/bash
# ============================================================================
#  build-app.sh — 把源码打包成双击即用的 NetPuff.app（macOS）
# ============================================================================
#
#  产物是「自包含」的 .app：一个 zsh 启动器 + 内嵌的 netpuff.py。
#  双击后自动寻找带 tkinter 的 Python 并启动 GUI，对方机器无需本项目源码、
#  也无需 pip install 任何东西。
#
#  用法：
#     ./app/build-app.sh            → 产物放在项目根目录（CI 依赖这个默认值）
#     ./app/build-app.sh dist       → 产物收进 dist/，保持根目录整洁
#
#  说明：本脚本只做「组装」，不做编译（Python 是解释型，无需编译）。
# ============================================================================
set -euo pipefail

# 定位项目根目录（本脚本位于 <root>/app/ 下）
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/src/netpuff.py"

# 输出目录：默认项目根目录；也可传一个目录（相对路径按项目根目录解析），
# 把构建产物收进 dist/ 之类的地方，避免根目录堆满 .app 与压缩包。
OUT="${1:-.}"
case "$OUT" in
  /*) ;;                      # 绝对路径，原样使用
  .)  OUT="$ROOT" ;;          # 默认：项目根目录（CI 依赖这个默认值）
  *)  OUT="$ROOT/$OUT" ;;     # 相对路径按项目根目录解析
esac
mkdir -p "$OUT"
APP="$OUT/NetPuff.app"

# 版本号从源码的 APP_VERSION 读取，保持「唯一来源」，避免与 CHANGELOG 不一致
VERSION="$(sed -n 's/^APP_VERSION = "\(.*\)".*/\1/p' "$SRC")"
if [ -z "$VERSION" ]; then
  echo "错误：无法从 $SRC 读取 APP_VERSION" >&2
  exit 1
fi
echo "==> 版本号：$VERSION"

echo "==> 清理旧的 .app（如存在）"
rm -rf "$APP"

echo "==> 创建 .app 目录结构"
mkdir -p "$APP/Contents/MacOS"
mkdir -p "$APP/Contents/Resources"

echo "==> 写入 Info.plist"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>NetPuff</string>
    <key>CFBundleDisplayName</key>
    <string>NetPuff</string>
    <key>CFBundleIdentifier</key>
    <string>io.github.hengjunguo35-oss.netpuff</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundleExecutable</key>
    <string>NetPuff</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

echo "==> 写入启动器脚本"
cat > "$APP/Contents/MacOS/NetPuff" <<'LAUNCHER'
#!/bin/zsh
# NetPuff 启动器（macOS）
# 自动寻找带 tkinter 的 Python 并启动 GUI

BIN="$(cd "$(dirname "$0")" && pwd)"
CONTENTS="$(dirname "$BIN")"
SCRIPT="$CONTENTS/Resources/netpuff.py"

# 候选 Python 列表（按优先级）
# 只检查 `import tkinter` 不够：系统自带 / Xcode 的 python3.9 能 import 成功，
# 但其 Tk 为 8.5，创建窗口时会直接崩溃。故校验 Tk 版本 >= 8.6。
for PY in "$HOME/.local/bin/python3.11" python3.11 python3.12 python3.10 python3; do
  if "$PY" -c "import tkinter,sys;sys.exit(0 if tkinter.TkVersion>=8.6 else 1)" >/dev/null 2>&1; then
    exec "$PY" "$SCRIPT"
  fi
done

# 未找到：弹窗提示
osascript -e 'display alert "未找到可用的 Python" message "请安装 Python（https://www.python.org/downloads/），安装时保持默认勾选 tcl/tk。"' >/dev/null 2>&1
exit 1
LAUNCHER

echo "==> 内嵌源码"
cp "$SRC" "$APP/Contents/Resources/netpuff.py"

echo "==> 赋可执行权限"
chmod +x "$APP/Contents/MacOS/NetPuff"

echo "==> 完成：$APP"
echo "    双击即可启动；若提示无法验证开发者，请："
echo "    xattr -dr com.apple.quarantine '$APP'"
