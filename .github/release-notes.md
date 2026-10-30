## NetPuff · 发行版

跨平台系统代理切换器。本页同时提供 **macOS** 与 **Windows** 发行包。

> ⚠️ 本程序仅供合法用途，请遵守你所在国家/地区的法律法规。详见仓库中的免责声明与 LICENSE（MIT）。

### 下载

| 文件 | 平台 | 说明 |
|---|---|---|
| `NetPuff-*-macOS.zip` | macOS | 内含 `NetPuff.app`，解压即用 |
| `NetPuff-*.dmg` | macOS | 磁盘映像，内含 `NetPuff.app` 与 `/Applications` 快捷方式 |
| `NetPuff-*-Windows.zip` | Windows | ⚠️ **功能尚未完善，不建议日常使用**，详见下文 |
| `SHA256SUMS.txt` | — | 校验和：`shasum -a 256 -c SHA256SUMS.txt` |

### macOS：安装与运行

1. 下载 `.dmg` 或 `.zip`，取出 `NetPuff.app`。
2. **首次打开会被 Gatekeeper 拦截**——本应用未做代码签名与公证。二选一：
   - 右键点击 `NetPuff.app` → **打开** → 在弹窗中再次点「打开」（每个应用只需一次）
   - 或在终端执行：`xattr -dr com.apple.quarantine /路径/NetPuff.app`
3. **前提：系统已安装带 `tkinter` 的 Python 3**（3.10 / 3.11 / 3.12）
   - 推荐 [python.org](https://www.python.org/downloads/) 的安装包（自带 Tcl/Tk）
   - ⚠️ **不要用 macOS 自带的 `python3`**：Xcode 版 Tk 过旧，创建窗口时会直接崩溃
   - 自检：`python3.11 -c "import tkinter; print(tkinter.TkVersion)"`，结果需 ≥ 8.6
4. 本程序**不打包 Python 运行时**——`.app` 只是一个启动器 + 内嵌脚本，零第三方依赖。

### Windows：⚠️ 功能尚未完善，不建议日常使用

提供该包的用途是让**开发者**能够直接解压、运行、修改并提交贡献。

- **前提**：已安装 Python 3（3.10 / 3.11 / 3.12），安装时勾选 `Add python.exe to PATH`
- **使用**：解压后双击 `app\start-netpuff.bat`
- **⚠️ 未经实机功能测试**：注册表读写、Wininet 刷新、`setx`、以及退出时的原生确认框
  （MessageBoxW）都只通过了静态检查与 CI 上的命令行冒烟验证（语法、CLI、
  SOCKS5/HTTP 端到端、`.bat` 行尾），**没有在真实 Windows 桌面上完整走过一遍**。
- **其他已知问题**
  - 系统 SOCKS 依赖 IE 设置：只有遵循系统代理的程序生效（Chrome / Edge 会；Firefox 默认不跟随；部分原生程序不遵循）
  - 终端代理只对**新开的**终端生效
- **参与贡献**：相关代码集中在 `src/netpuff.py` 的 `IS_WIN` 分支——
  `set_system_proxy()` / `clear_system_proxy()`、`set_terminal_proxy()` / `clear_terminal_proxy()`、
  `get_proxy_status()` / `get_proxy_detail()`、`_win_refresh()`，以及 `on_close()` 的 Windows 分支
- 包内 `README-Windows.txt` 有完整说明

### 关于新行为

完整改动见 **[CHANGELOG.md](https://github.com/hengjunguo35-oss/NetPuff/blob/main/CHANGELOG.md)**。

- **退出保护**：系统代理仍开启时关闭窗口，会弹系统级确认框——
  「恢复直连并退出」/「仅退出软件」/「取消」。代理已关则不再弹窗。
- **启动自检**：打开软件即扫描系统代理；若仍在代理，状态栏直接显示「⚠ 正在代理」
  并回填检测到的地址，点「取消代理 / 恢复直连」一键关闭。

### 共同说明

- 本程序**不提供代理服务、不承载或中转任何流量、不内置任何节点**；它连接的是**你自己提供的**代理服务器。
- 历史记录与配置仅保存在本机：`~/.netpuff_history.json`、`~/.netpuff_config.json`。

---

<sub>AI-translated from the Chinese original, provided for reference only. The Chinese version is authoritative.</sub>

## NetPuff · Releases

Cross-platform system proxy switcher. Both **macOS** and **Windows** packages are provided on this page.

> ⚠️ For lawful use only — please comply with the laws of your country/region. See the disclaimer and LICENSE (MIT) in the repository.

### Download

| File | Platform | Notes |
|---|---|---|
| `NetPuff-*-macOS.zip` | macOS | Contains `NetPuff.app` |
| `NetPuff-*.dmg` | macOS | Disk image containing `NetPuff.app` and an `/Applications` shortcut |
| `NetPuff-*-Windows.zip` | Windows | ⚠️ **Not yet complete — not recommended for daily use.** See below |
| `SHA256SUMS.txt` | — | Checksums: `shasum -a 256 -c SHA256SUMS.txt` |

### macOS: install & run

1. Download the `.dmg` or `.zip` and take out `NetPuff.app`.
2. **Gatekeeper blocks the first launch** — the app is not code-signed or notarized. Either:
   - Right-click `NetPuff.app` → **Open** → click **Open** again in the dialog (once per app), or
   - Run: `xattr -dr com.apple.quarantine /path/to/NetPuff.app`
3. **Requires Python 3 with `tkinter`** (3.10 / 3.11 / 3.12). Prefer the
   [python.org](https://www.python.org/downloads/) installer (bundles Tcl/Tk).
   ⚠️ **Do not use the system `python3`** — its Tk is too old and crashes when creating a
   window. Check with `python3.11 -c "import tkinter; print(tkinter.TkVersion)"` (needs ≥ 8.6).
4. **No Python runtime is bundled** — the `.app` is a launcher plus the embedded script,
   with zero third-party dependencies.

### Windows: ⚠️ not yet complete — not recommended for daily use

This package exists so that **developers** can unzip it, run it, patch it, and submit changes.

- **Requires** Python 3 (3.10 / 3.11 / 3.12) installed with `Add python.exe to PATH` ticked
- **Usage**: unzip, then double-click `app\start-netpuff.bat`
- **⚠️ NOT functionally tested on real hardware**: registry read/write, the Wininet refresh,
  `setx`, and the native quit confirmation (MessageBoxW) have only passed static checks and
  CI smoke tests (syntax, CLI, SOCKS5/HTTP end-to-end, `.bat` line endings) — **they have
  never been exercised end-to-end on a real Windows desktop**.
- **Other known issues**
  - System SOCKS relies on IE settings: only programs that follow the system proxy are
    affected (Chrome / Edge do; Firefox does not by default; some native apps do not)
  - The terminal proxy only affects **newly opened** terminals
- **Contributing**: the Windows-specific code lives in the `IS_WIN` branches of
  `src/netpuff.py` — `set_system_proxy()` / `clear_system_proxy()`,
  `set_terminal_proxy()` / `clear_terminal_proxy()`, `get_proxy_status()` /
  `get_proxy_detail()`, `_win_refresh()`, plus the Windows branch of `on_close()`
- See `README-Windows.txt` inside the package for the full notes

### New behaviour

Full change history: **[CHANGELOG.en.md](https://github.com/hengjunguo35-oss/NetPuff/blob/main/CHANGELOG.en.md)**.

- **Quit protection**: closing the window while the system proxy is still on raises a native
  dialog — "restore and quit" / "quit only" / "cancel". No dialog when the proxy is already off.
- **Startup self-check**: the app scans the system proxy on launch; if one is still active the
  status bar shows "⚠ proxying", the detected address is filled in, and
  "cancel proxy / restore direct" disables it in one click.

### Common notes

- This program **provides no proxy service, carries or relays no traffic, and bundles no
  nodes**; it connects to a proxy server **that you supply yourself**.
- History and config are stored only on your machine: `~/.netpuff_history.json`,
  `~/.netpuff_config.json`.
