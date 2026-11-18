## NetPuff 1.2.0 · Windows 兼容模式与安装包

这个版本的重点是 **Windows 真正可用**：解决「系统代理只认 SOCKS4、被墙域名打不开」，
并补上配置备份/还原、终端变量和安装包。

### 🪟 Windows 兼容模式（默认开启）

Windows 的系统代理只会发 SOCKS4，而 SOCKS4 要求在本地解析域名；被污染的域名会解析成
错误 IP，代理自然连不上。

现在连接 SOCKS5 时，NetPuff 会在本机 `127.0.0.1` 启动一个 **HTTP→SOCKS5 转换器**，
系统代理指向本机；HTTPS 走 CONNECT，把**域名**交给上游解析：

```
浏览器 ──CONNECT x.com:443──▶ 127.0.0.1:随机端口 ──SOCKS5(域名)──▶ 上游代理
```

- 实测系统层可直接打开 **x.com / google.com**；
- 只监听本机回环，不经过第三方；断开时转换器自动结束；
- 设置 `NETPUFF_NO_BRIDGE=1` 可退回纯 SOCKS4 模式。

### 🔐 先备份，再写入，断开精确还原

注册表四项（`ProxyEnable / ProxyServer / ProxyOverride / AutoConfigURL`）与 8 个代理
环境变量会先快照到 `~/.netpuff_win_state.json`；断开时只还原「仍然是我们写入的值」，
期间被你改过的项保留并提示。没有快照时只关开关，绝不猜你原来的地址。

### 🧹 终端代理重写

不再用 `setx`（会留下空变量、有 `SUCCESS:` 噪音），改为写 `HKCU\Environment` 并广播；
8 个变量（含大小写与 `no_proxy`）；清理时只删自己写的值，你原有的公司代理会恢复。
`connect` 不带 `-t` 时不再清空终端代理。

### 🛠 其他修复

- CLI：端口非法、协议失败不再抛 traceback；参数错误退出码 2，运行失败 3；
  `status` 关闭态不再打印服务器地址。
- 探测按 `Content-Length` 读取，避免服务端 keep-alive 导致 15 秒超时。
- 支持 `[IPv6]:端口`。
- GUI：高 DPI 感知、Windows 字体/主题、状态栏换行、取消按钮初始禁用、
  退出确认框传入父窗口；应用与窗口统一使用新图标。

---

## 📦 安装包 · Installation packages

| 文件 File | 平台 Platform | 说明 Description |
|---|---|---|
| **NetPuff-1.2.0-Setup.exe** | Windows | **推荐**：向导安装，按用户安装（无需管理员），自动建开始菜单快捷方式 |
| NetPuff.exe | Windows | 便携版：单文件，双击即用，不需要安装 Python |
| **NetPuff-1.2.0.dmg** | macOS | **推荐**：双击打开后把 App 拖进「应用程序」（由 CI 在 macOS 上构建） |
| NetPuff-1.2.0-macOS.zip | macOS | 备用：解压即得 `NetPuff.app` |
| SHA256SUMS.txt | — | 校验和：`shasum -a 256 -c SHA256SUMS.txt` |

**Windows 要求**：Windows 10/11 x64；安装包与便携版**不需要安装 Python**。
**macOS 要求**：Python 3.10–3.13（含 `tkinter` ≥ 8.6），不打包 Python 运行时。

> Windows 安装包与 exe 未做代码签名，SmartScreen 可能提示「未知发布者」，
> 点「更多信息 → 仍要运行」即可。
> macOS 应用未签名，首次打开需右键 → 打开，或执行
> `xattr -dr com.apple.quarantine /Applications/NetPuff.app`。

---

## ⚠️ 首次打开被 macOS 拦截？· Gatekeeper

本程序没有 Apple 开发者签名，macOS 会提示「无法验证开发者」。

**方法一**：右键点 App → 选择「打开」→ 再点「打开」（只需一次）。
**方法二**：`xattr -dr com.apple.quarantine /Applications/NetPuff.app`

⚠️ **不要用 macOS 自带的 `python3`**——Xcode 版 Tk 过旧，创建窗口时会崩溃。
自检：`python3.11 -c "import tkinter; print(tkinter.TkVersion)"`，结果需 ≥ 8.6。

---

## ✨ English summary

NetPuff 1.2.0 makes Windows genuinely usable:

- **Compatibility mode (on by default)**: Windows only speaks SOCKS4 and resolves DNS
  locally, so blocked domains fail. NetPuff now runs a local HTTP→SOCKS5 bridge on
  `127.0.0.1`; HTTPS uses CONNECT so the upstream resolves host names. Verified to open
  x.com / google.com through the system proxy. Loopback only; stopped on disconnect;
  disable with `NETPUFF_NO_BRIDGE=1`.
- **Snapshot / restore**: four registry values and eight environment variables are saved
  before writing and restored exactly on disconnect (only values still ours; user edits
  are kept). Without a snapshot it only turns the switch off.
- **Terminal proxy**: written via `HKCU\Environment` + `WM_SETTINGCHANGE`, eight variables
  including `no_proxy`, owned values only; `-t` semantics fixed.
- **CLI/GUI**: readable errors instead of tracebacks, `Content-Length`-aware probing,
  IPv6 `[addr]:port`, DPI awareness, new app icon, and installer packaging.

Assets: Windows `NetPuff-1.2.0-Setup.exe` / portable `NetPuff.exe`; macOS
`NetPuff-1.2.0.dmg` / `NetPuff-1.2.0-macOS.zip`; `SHA256SUMS.txt`.

---

**本程序不提供代理服务、不中转第三方流量、不内置任何节点**——你连的是你自己的代理。
Windows 兼容模式仅在本机 `127.0.0.1` 做协议转换。

历史记录与配置仅保存在本机：`~/.netpuff_history.json`、`~/.netpuff_config.json`。

许可证 License：MIT · 仅供合法用途。
