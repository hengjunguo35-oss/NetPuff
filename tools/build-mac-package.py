#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨平台构建 macOS 的 NetPuff.app 压缩包。

macOS 的 .app 本质是目录 + Info.plist + 可执行启动器；压缩包用 Python
写入正确的 Unix 权限位，因此在 Windows / Linux 上也能产出可用的 zip。
dmg 仍需要 macOS（hdiutil），这里只做 zip。
"""
import os
import re
import sys
import time
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")


def app_version():
    text = open(os.path.join(ROOT, "src", "netpuff.py"), encoding="utf-8").read()
    match = re.search(r'^APP_VERSION = "([^"]+)"', text, re.M)
    if not match:
        raise SystemExit("无法从 src/netpuff.py 读取 APP_VERSION")
    return match.group(1)


def add(zf, name, data, mode):
    info = zipfile.ZipInfo(name, date_time=time.localtime()[:6])
    info.external_attr = (mode & 0xFFFF) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, data)


def main():
    version = app_version()
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "NetPuff-%s-macOS.zip" % version)

    plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>NetPuff</string>
    <key>CFBundleDisplayName</key><string>NetPuff</string>
    <key>CFBundleIdentifier</key><string>io.github.hengjunguo35-oss.netpuff</string>
    <key>CFBundleVersion</key><string>{v}</string>
    <key>CFBundleShortVersionString</key><string>{v}</string>
    <key>CFBundleExecutable</key><string>NetPuff</string>
    <key>CFBundleIconFile</key><string>NetPuff.icns</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
""".format(v=version)

    launcher = """#!/bin/zsh
# NetPuff 启动器（macOS）
BIN="$(cd "$(dirname "$0")" && pwd)"
CONTENTS="$(dirname "$BIN")"
SCRIPT="$CONTENTS/Resources/netpuff.py"

for PY in "$HOME/.local/bin/python3.11" python3.11 python3.12 python3.10 python3; do
  if "$PY" -c "import tkinter,sys;sys.exit(0 if tkinter.TkVersion>=8.6 else 1)" >/dev/null 2>&1; then
    exec "$PY" "$SCRIPT"
  fi
done

osascript -e 'display alert "未找到可用的 Python" message "请安装 Python（https://www.python.org/downloads/），安装时保持默认勾选 tcl/tk。"' >/dev/null 2>&1
exit 1
"""

    base = "NetPuff.app"
    files = [
        (base + "/Contents/Info.plist", plist.encode("utf-8"), 0o100644),
        (base + "/Contents/MacOS/NetPuff", launcher.encode("utf-8"), 0o100755),
        (base + "/Contents/Resources/netpuff.py",
         open(os.path.join(ROOT, "src", "netpuff.py"), "rb").read(), 0o100644),
        (base + "/Contents/Resources/NetPuff.icns",
         open(os.path.join(ROOT, "app", "netpuff.icns"), "rb").read(), 0o100644),
        (base + "/Contents/Resources/app/netpuff-256.png",
         open(os.path.join(ROOT, "app", "netpuff-256.png"), "rb").read(), 0o100644),
    ]

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for directory in (base, base + "/Contents", base + "/Contents/MacOS",
                          base + "/Contents/Resources", base + "/Contents/Resources/app"):
            add(zf, directory + "/", b"", 0o40755)
        for name, data, mode in files:
            add(zf, name, data, mode)

    print("built:", out, os.path.getsize(out), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
