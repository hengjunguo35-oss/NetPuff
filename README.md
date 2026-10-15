# NetPuff

> 一个免费、开源的跨平台系统代理切换器 · **macOS / Windows**

> 🌐 English version: **[README.en.md](README.en.md)**　·　📋 [更新日志](CHANGELOG.md)

> ⚠️ **仅供个人学习、研究与交流使用。** 使用前请阅读 [免责声明与使用条款](免责声明.md) 与 [LICENSE](LICENSE)（MIT）。

> ⚠️ **Windows 平台尚未完善，暂不建议使用。** Windows 分支（注册表 + Wininet）未经充分
> 实机验证，可能存在兼容性问题；如确有需要，欢迎自行拉取代码修改适配。

在「直连」和「代理」之间一键切换的小工具：填好代理服务器地址，点一下就连上，
自动验证代理是否真的通了、出口在哪；再点一下就恢复直连。命令行里也能用。

**它不承载任何流量转发**——真正的出口是你自己的内网 SOCKS5 服务器，
NetPuff 只负责把「开关」拨到位，并用一个真实的请求替你验证拨没拨对。

---

## 起因

手里有一台内网代理，但每次都要在系统设置里手动填 SOCKS5 地址、
换网络后 IP 还老变，来回折腾。

而且填完到底通没通、出口在哪、有没有偷偷还走直连，系统设置里**看不出来**。

那就不如自己写一个：填地址 → 验证 → 切换，一条龙，出口 IP 明明白白显示出来。

---

## 能做什么

| 功能 | 说明 |
|---|---|
| 一键连接 / 断开 | GUI 点按钮，或命令行 `connect` / `disconnect` |
| 三种协议 | SOCKS5 / HTTP / HTTPS（默认 SOCKS5） |
| 连接前先验证 | 先走代理发一个真实请求，确认出口可用才写系统配置 |
| 出口可视化 | 显示出口 IP、国家/地区/城市、运营商、延迟 |
| 系统代理 | macOS `networksetup`；Windows 注册表 + Wininet 刷新 |
| 终端代理 | 同时写 `http_proxy` 等环境变量，让 curl / pip / git 也走代理 |
| 直连确认 | 取消后查询本机真实出口，确认真的回到直连 |
| 历史记忆 | 记住连过的 IP，下拉直接选 |

**不做的事**：不提供代理服务、不中转流量、不内置任何节点。你连的是你自己的代理。

---

## 环境要求

- macOS 10.13+（主要支持平台）
- Windows 7+ —— **尚未完善，暂不建议使用**（详见[技术文档 · 已知限制](技术文档.md)）
- 一个带 **tkinter** 的 Python 3（3.10 / 3.11 / 3.12 均可）
  - macOS 建议用 [python.org](https://www.python.org/downloads/) 的安装包（自带 Tcl/Tk）
  - Windows 安装时务必勾选 **"Add python.exe to PATH"**
- **零第三方依赖**：只用 Python 标准库

---

## 快速开始

### macOS

```bash
# 直接跑 GUI
python3 src/netpuff.py

# 或命令行连接（连接 + 终端代理一起开）
python3 src/netpuff.py connect 192.168.1.100 2080 -t

# 恢复直连
python3 src/netpuff.py disconnect
```

双击即用的 `.app` 可以自己打包：

```bash
./app/build-app.sh          # 生成 NetPuff.app，双击即用
```

### Windows

> ⚠️ **尚未完善，暂不建议使用。** 以下内容仅供参考，未经充分实机验证；
> 欢迎自行拉取代码修改适配。

```
双击  app\启动NetPuff.bat
```

> 前提是 `python` 或 `pythonw` 已在 PATH 里（装 Python 时勾选 "Add python.exe to PATH"）。

---

## 命令行用法

```
python3 src/netpuff.py status                 # 查看系统代理状态
python3 src/netpuff.py test  <IP> [端口]       # 只测试代理，不改系统设置
python3 src/netpuff.py connect <IP> [端口] [-t] # 测试并开启系统代理；-t 同时设终端代理
python3 src/netpuff.py disconnect              # 恢复直连
python3 src/netpuff.py direct                  # 查看本机直连出口 IP
```

`-p socks5|http|https` 可指定协议（默认 socks5）。

---

## 它是怎么工作的（简述）

1. **探针**：先用裸 socket 走 SOCKS5/HTTP 代理访问 ip-api.com，拿到出口 IP
   与地理位置，并测出延迟。**这一步先于设置系统代理**——确认代理可用才动手。
2. **系统代理**：macOS 调 `networksetup`；Windows 写注册表并让 Wininet 刷新。
3. **终端代理**：向 shell rc 或用户环境变量写 `http_proxy` 等，带内网 `no_proxy` 白名单。
4. **取消**：反向清空，恢复直连。

核心难点在于 **SOCKS5 协议要自己手写**——Python 标准库的 urllib 不认 socks 代理，
为保持零依赖，用裸 socket 实现了 RFC 1928 的握手。详见 [技术文档.md](技术文档.md)。

---

## 排错

| 现象 | 处理 |
|---|---|
| 报「端口未开放」 | 代理服务器没启动，或 IP 换了。先 `test <IP>` 确认 |
| 换网络后连不上 | 内网代理 IP 会随网络变化，更新成当前网段的 IP 再连 |
| 终端里 curl 没走代理 | 终端代理只对**新开的 shell**生效；`source ~/.zshrc` 或重开终端 |
| Windows 下个别程序不走代理 | 系统 SOCKS 依赖 IE 设置，部分程序不遵循（见技术文档·已知限制） |
| 访问内网变慢/不通 | 检查 `no_proxy` 是否覆盖了内网网段 |

---

## 目录结构

```
src/netpuff.py        全部逻辑（单文件，逐函数带批注）
app/启动NetPuff.command    macOS 双击启动脚本
app/启动NetPuff.bat        Windows 双击启动脚本
app/build-app.sh              打包成 NetPuff.app
```

## 隐私

**本地工具，本身不收集、不上传任何信息。** 唯一一次联网是走代理查询
ip-api.com 的出口地理位置（为了显示「你现在从哪出去」）。除此之外
不连接任何服务器。历史记录只存在你本机 `~/.netpuff_history.json`。

## English summary

`NetPuff` is a cross-platform (macOS / Windows) system proxy switcher with a GUI and
CLI. It toggles between direct connection and a SOCKS5/HTTP/HTTPS proxy, verifies the
proxy actually works before applying it, and shows the real egress IP / geolocation /
latency. Zero third-party dependencies (Python standard library only); the SOCKS5
handshake (RFC 1928) is implemented from scratch over raw sockets.

---

## License

**MIT** — 见 [LICENSE](LICENSE)。可自由使用、修改、分发，保留版权署名即可。
