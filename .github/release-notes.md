## 🆕 本次新增两个功能：不再把代理忘在系统里 · Two new features

### 1. 退出保护：关窗口前先问你一句

以前关掉软件，系统代理还留着——直到下次上网才发现流量还在绕，或者干脆忘了这回事。

**场景**：连上代理，用完直接点窗口右上角关闭。软件没了，代理还在系统里生效。

**做法**：关窗口时先读一次**真实的系统状态**（不是内存里的标志位），若代理还开着，
弹一个系统级确认框：

| 选项 Option | 行为 Behaviour |
|---|---|
| **恢复直连并退出** | 先清掉系统代理 + 终端代理，再退出 |
| **仅退出软件** | 保留代理，只关软件 |
| **取消** | 留在软件里 |

代理已关闭时**不弹窗**，不打扰。

**为什么是三个按钮而不是「是 / 否」**：macOS 的 `display alert` 里，点「取消类按钮」和按 Esc
返回值完全一样，二选一无法区分，会把「仅退出」误判成「取消」。加一个独立的「取消」才能三者分明。

**macOS 的额外处理**：Cmd+Q 不走窗口关闭事件（`WM_DELETE_WINDOW`），所以另外接管了
`::tk::mac::Quit`——否则用快捷键退出会绕过整个确认。

**Why three buttons instead of Yes/No**: in macOS `display alert`, clicking the cancel button and
pressing Esc return exactly the same value, so a two-button dialog cannot tell "quit only" from
"cancel". A separate Cancel button is the only way to keep the three outcomes distinct.
On macOS, Cmd+Q does not go through `WM_DELETE_WINDOW`, so `::tk::mac::Quit` is hooked as well —
otherwise the shortcut would bypass the confirmation entirely.

### 2. 启动自检：打开就知道现在还在代理

接上面的「仅退出软件」——过一段时间想把代理关掉，还得去系统设置里手动改。

**做法**：打开软件 400ms 后，在后台线程扫描系统代理配置。若仍在代理：

- 状态栏直接切成「⚠ 检测到系统代理仍开启 · 地址:端口」
- 把探测到的地址 / 端口 / 协议**回填进表单**
- 再异步探测出口：成功则显示「⚠ 正在代理 · 出口 IP · 国家 城市」；失败则显示「探测失败」，仍可关闭
- 关闭入口就是原有的「取消代理 / 恢复直连」按钮——**没有新增任何控件**

**How it works**: 400 ms after launch a worker thread scans the system proxy configuration. If a
proxy is still active, the status bar switches to "⚠ system proxy still enabled · host:port", the
detected address / port / protocol are filled into the form, and the egress is probed
asynchronously. The disconnect entry point is the existing
"cancel proxy / restore direct" button — **no new widgets**.

### 修复：macOS 对话框差点弹不出来 · A dialog that nearly failed to compile

第一版用了 `with icon caution`——那是 `display dialog` 的参数，`display alert` 不认，
脚本**编译失败**。用 `osacompile` 校验时才发现，已改为 `as warning`。
若没有这一步校验，这个功能会在 macOS 上安静地失效。

The first version used `with icon caution`, a `display dialog` parameter that `display alert`
rejects — the script **failed to compile**. Caught by validating with `osacompile`; now uses
`as warning`. Without that check the feature would have silently done nothing on macOS.

---

## 📦 安装包 · Installation packages

| 文件 File | 平台 Platform | 说明 Description |
|---|---|---|
| **NetPuff-{{VERSION}}.dmg** | macOS | **推荐 Recommended** — 双击打开后，把 App 拖进「应用程序」文件夹 / Open it and drag the app into Applications |
| NetPuff-{{VERSION}}-macOS.zip | macOS | 备用 Alternative — 解压即得 `.app` / Unzip to get the `.app` |
| NetPuff-{{VERSION}}-Windows.zip | Windows | ⚠️ **功能尚未完善，未经实机测试** / not yet complete, untested |
| SHA256SUMS.txt | — | 校验和 Checksums — `shasum -a 256 -c SHA256SUMS.txt` |

**系统要求 Requirements**：macOS + Python 3.10 / 3.11 / 3.12（含 `tkinter` ≥ 8.6）
**Windows**：Python 3.10 / 3.11 / 3.12，安装时勾选 `Add python.exe to PATH`

> 本程序**不打包 Python 运行时**——`.app` 只是一个启动器 + 内嵌脚本，零第三方依赖。
> No Python runtime is bundled — the `.app` is a launcher plus the embedded script, with zero
> third-party dependencies.

---

## ⚠️ 首次打开被 macOS 拦截？· Gatekeeper blocking the first launch?

本程序没有 Apple 开发者签名，macOS 会提示「无法验证开发者」。
The app is not signed with an Apple Developer certificate, so macOS warns that the developer
cannot be verified.

**方法一 Option 1（推荐 Recommended）**
右键点 App → 选择「打开」→ 再点「打开」。只需一次。
Right-click the app → **Open** → **Open** again. Only needed once.

**方法二 Option 2**
```bash
xattr -dr com.apple.quarantine /Applications/NetPuff.app
```

⚠️ 另需注意：**不要用 macOS 自带的 `python3`**——Xcode 版 Tk 过旧，创建窗口时会直接崩溃。
自检：`python3.11 -c "import tkinter; print(tkinter.TkVersion)"`，结果需 ≥ 8.6。
Do **not** use the system `python3` — its Tk is too old and crashes when a window is created.

---

## ⚠️ Windows 版：未经实机测试 · Windows build: NOT tested on real hardware

提供这个包，是为了让开发者能直接解压、运行、修改并提交贡献。

- 注册表读写、Wininet 刷新、`setx`、退出确认框（MessageBoxW）**只通过静态检查与 CI 命令行冒烟验证**
  ——语法、CLI、SOCKS5/HTTP 端到端、`.bat` 行尾，**从未在真实 Windows 桌面完整走过一遍**
- 系统 SOCKS 依赖 IE 设置：只有遵循系统代理的程序生效（Chrome / Edge 会；Firefox 默认不跟随）
- 终端代理只对**新开的**终端生效
- 想参与贡献：相关代码在 `src/netpuff.py` 的 `IS_WIN` 分支——`set_system_proxy()` /
  `clear_system_proxy()`、`set_terminal_proxy()` / `clear_terminal_proxy()`、`get_proxy_status()` /
  `get_proxy_detail()`、`_win_refresh()`，以及 `on_close()` 的 Windows 分支

Registry read/write, the Wininet refresh, `setx`, and the native quit dialog (MessageBoxW) have only
passed static checks and CI smoke tests — they have **never** been exercised end-to-end on a real
Windows desktop. The Windows-specific code lives in the `IS_WIN` branches of `src/netpuff.py`.

---

## ✨ 其他 · Also in this release

新增 `get_proxy_detail()`：读取系统代理的协议 / 地址 / 端口，供启动自检与出口探测使用。
Windows 侧解析 `ProxyServer` 的多协议映射，按 socks > http > https 取优先级。

Adds `get_proxy_detail()`, which reads the system proxy protocol / address / port for the startup
self-check and egress probing (on Windows it parses multi-protocol `ProxyServer` maps, preferring
socks > http > https).

状态栏文本增加截断保护，避免过长提示被无声裁切。
Status-bar text is now truncated with an ellipsis instead of being silently clipped.

文档同步更新：CHANGELOG 中英双版、技术文档新增 2.6 节（两个机制的实现与踩过的坑）、
README 功能表与排错表、Windows 包内说明。
Documentation updated across both changelogs, the technical docs (new section 2.6), the README
feature and troubleshooting tables, and the Windows package notes.

---

**本程序不提供代理服务、不承载或中转任何流量、不内置任何节点**——你连的是你自己的代理。
**No proxy service, no traffic relay, no bundled nodes** — you connect to your own proxy.

历史记录与配置仅保存在本机：`~/.netpuff_history.json`、`~/.netpuff_config.json`。
History and config stay on your machine only.

许可证 License：MIT · 仅供合法用途，请遵守你所在国家/地区的法律法规 / For lawful use only.
