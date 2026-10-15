#!/bin/zsh
# NetPuff —— macOS 双击启动脚本（备用，等效于 NetPuff.app）

DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$DIR/../src/netpuff.py"

# 只检查 `import tkinter` 不够：系统自带 / Xcode 的 python3.9 能 import 成功，
# 但其 Tk 为 8.5，创建窗口时会直接崩溃。故校验 Tk 版本 >= 8.6。
for PY in "$HOME/.local/bin/python3.11" python3.11 python3.12 python3.10 python3; do
  if "$PY" -c "import tkinter,sys;sys.exit(0 if tkinter.TkVersion>=8.6 else 1)" >/dev/null 2>&1; then
    exec "$PY" "$SCRIPT"
  fi
done

osascript -e 'display alert "未找到可用的 Python" message "请安装 Python（https://www.python.org/downloads/），安装时保持默认勾选 tcl/tk。"' >/dev/null 2>&1
echo "未找到带 tkinter 的 Python，请安装 python.org 的 Python 后重试。"
read -n 1 -s
exit 1
