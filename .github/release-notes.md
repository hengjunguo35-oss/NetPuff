## NetPuff {{VERSION}} · 修复「下载后无法连接」

### 🔧 修复了两个最常见的原因

**1. IP 栏可以直接填 `IP:端口`**

之前把 `10.1.2.3:2080` 填进「服务器 IP」栏，程序会拼成 `10.1.2.3:2080:2080`，
然后报「端口未开放」。现在 CLI 和 GUI 都会自动拆分，也支持：

- `10.1.2.3:2080`
- `[2408::1]:2080`（IPv6）
- `socks5://10.1.2.3:2080`（带协议前缀）

**2. 出口查询失败不再阻断连接**

出口信息（国家/城市）依赖 ip-api.com。它被墙、限流或返回非 JSON 时，
以前的版本会直接拒绝连接。现在会改用 NCSI / example.com 验证代理隧道；
隧道通就继续写入系统代理，状态栏提示「出口信息查询失败」。

**其他**

- Windows 不再显示 `https` 协议（WinINet 没有 TLS 连代理概念），CLI 会给出明确错误；
- 「端口未开放」提示补充「IP 栏只填地址、端口填在端口栏」；
- 发行流程不再生成旧的 `Windows.zip` 源码包。

### 🪟 Windows 兼容模式（默认开启）

Windows 系统代理只认 SOCKS4、且本地解析域名；兼容模式在本机 `127.0.0.1`
起一个 HTTP→SOCKS5 转换器，让域名交给上游解析。只监听本机回环，断开时自动停止。
设置 `NETPUFF_NO_BRIDGE=1` 可退回纯 SOCKS4 模式。

---

## 📦 安装包 · Installation packages

| 文件 File | 平台 Platform | 说明 Description |
|---|---|---|
| **NetPuff-{{VERSION}}-Setup.exe** | Windows | **推荐**：向导安装，按用户安装（无需管理员），自动建开始菜单快捷方式 |
| NetPuff.exe | Windows | 便携版：单文件，双击即用，不需要安装 Python |
| **NetPuff-{{VERSION}}-macOS.zip** | macOS | **推荐**：解压即得 `NetPuff.app`，拖进「应用程序」 |
| NetPuff-{{VERSION}}.dmg | macOS | 可选：由 macOS 上的手动 Release 工作流生成，不是每次都有 |
| SHA256SUMS.txt | — | 校验和：`shasum -a 256 -c SHA256SUMS.txt` |

**Windows 要求**：Windows 10/11 x64；安装包与便携版**不需要安装 Python**。
**macOS 要求**：Python 3.10–3.13（含 `tkinter` ≥ 8.6），不打包 Python 运行时。

> Windows 安装包与 exe 未做代码签名，SmartScreen 可能提示「未知发布者」，
> 点「更多信息 → 仍要运行」即可。

---

## ⚠️ macOS 首次打开被拦截？

本程序没有 Apple 开发者签名，macOS 会提示「无法验证开发者」。

**方法一**：右键点 App → 选择「打开」→ 再点「打开」（只需一次）。
**方法二**：`xattr -dr com.apple.quarantine /Applications/NetPuff.app`

⚠️ 不要用 macOS 自带的 `python3`——Xcode 版 Tk 过旧，创建窗口时会崩溃。
自检：`python3.11 -c "import tkinter; print(tkinter.TkVersion)"`，结果需 ≥ 8.6。

---

## ✨ English summary

NetPuff {{VERSION}} fixes the two most common "downloaded but cannot connect" causes:

- the IP field now accepts `IP:port` (and `[IPv6]:port`, `socks5://host:port`);
- a failed egress lookup no longer blocks connecting — NetPuff verifies the proxy tunnel
  via NCSI / example.com and proceeds when it works;
- `https` is hidden on Windows (no TLS-to-proxy in WinINet);
- clearer "port not open" guidance; the obsolete source `Windows.zip` is gone.

Windows ships `NetPuff-{{VERSION}}-Setup.exe` and portable `NetPuff.exe` (no Python needed);
macOS ships `NetPuff-{{VERSION}}-macOS.zip`; a `.dmg` is optional and only produced by a
manual macOS run.

---

**本程序不提供代理服务、不中转第三方流量、不内置任何节点**——你连的是你自己的代理。
Windows 兼容模式仅在本机 `127.0.0.1` 做协议转换。

历史记录与配置仅保存在本机：`~/.netpuff_history.json`、`~/.netpuff_config.json`。

许可证 License：MIT · 仅供合法用途。
