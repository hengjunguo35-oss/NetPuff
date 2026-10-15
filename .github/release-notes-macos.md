## NetPuff · macOS 发行版

跨平台系统代理切换器。本次发布为 **macOS** 版；**Windows 分支尚未完善，暂不提供发行包**。

> ⚠️ 本程序仅供合法用途，请遵守你所在国家/地区的法律法规。详见仓库中的免责声明与 LICENSE（MIT）。

### 下载

| 文件 | 说明 |
|---|---|
| `NetPuff-*-macOS.zip` | 内含 `NetPuff.app`，解压即用 |
| `SHA256SUMS.txt` | 校验和（可用 `shasum -a 256 -c SHA256SUMS.txt` 核对） |

### 安装与运行

1. 下载 zip 并解压，得到 `NetPuff.app`。
2. **首次打开会被 Gatekeeper 拦截**——本应用未做代码签名与公证。二选一：
   - 右键点击 `NetPuff.app` → **打开** → 在弹窗中再次点「打开」（每个应用只需一次）
   - 或在终端执行：`xattr -dr com.apple.quarantine /路径/NetPuff.app`
3. **前提：系统已安装带 `tkinter` 的 Python 3**（3.10 / 3.11 / 3.12）
   - 推荐 [python.org](https://www.python.org/downloads/) 的安装包（自带 Tcl/Tk）
   - ⚠️ **不要用 macOS 自带的 `python3`**：Xcode 版 Tk 过旧，创建窗口时会直接崩溃。
     可先自检：`python3.11 -c "import tkinter; print(tkinter.TkVersion)"`，结果需 ≥ 8.6
4. 本程序**不打包 Python 运行时**——`.app` 只是一个启动器 + 内嵌脚本，零第三方依赖。

### 使用

- **GUI**：双击 `NetPuff.app` → 填代理服务器地址与端口 → 选协议 → 「连接代理」
- **命令行**：见仓库 README

### 说明

- 本程序**不提供代理服务、不承载或中转任何流量、不内置任何节点**；它连接的是**你自己提供的**代理服务器。
- 历史记录与配置仅保存在本机 `~/.netpuff_history.json` / `~/.netpuff_config.json`。

---

<sub>AI-translated from the Chinese original, provided for reference only. The Chinese version is authoritative.</sub>

## NetPuff · macOS release

Cross-platform system proxy switcher. This is the **macOS** release. **Windows support is not yet complete, so no Windows package is provided.**

> ⚠️ For lawful use only. See the disclaimer and LICENSE (MIT) in the repository.

### Download

| File | Notes |
|---|---|
| `NetPuff-*-macOS.zip` | Contains `NetPuff.app` |
| `SHA256SUMS.txt` | Checksums (`shasum -a 256 -c SHA256SUMS.txt`) |

### Install & run

1. Download the zip and extract `NetPuff.app`.
2. **Gatekeeper blocks the first launch** — the app is not code-signed or notarized. Either:
   - Right-click `NetPuff.app` → **Open** → click **Open** again in the dialog (once per app), or
   - Run: `xattr -dr com.apple.quarantine /path/to/NetPuff.app`
3. **Requires Python 3 with `tkinter`** (3.10 / 3.11 / 3.12). Prefer the
   [python.org](https://www.python.org/downloads/) installer (bundles Tcl/Tk).
   ⚠️ **Do not use the system `python3`** — its Tk is too old and crashes when creating a
   window. Check with `python3.11 -c "import tkinter; print(tkinter.TkVersion)"` (needs ≥ 8.6).
4. **No Python runtime is bundled** — the `.app` is a launcher plus the embedded script, with
   zero third-party dependencies.

### Usage

- **GUI**: double-click `NetPuff.app` → enter your proxy address and port → pick a protocol → Connect.
- **CLI**: see the repository README.

### Notes

- This program **provides no proxy service, carries or relays no traffic, and bundles no nodes**;
  it connects to a proxy server **that you supply yourself**.
- History and config are stored only on your machine (`~/.netpuff_history.json`,
  `~/.netpuff_config.json`).
