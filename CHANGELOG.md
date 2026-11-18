# 更新日志 · Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

> 🌐 英文版（[CHANGELOG.en.md](CHANGELOG.en.md)）由 AI（**DeepSeek Harness**）自中文原文
> 翻译，仅供参考；如与中文版有出入，以中文版为准。

---

## [1.2.0] — 2026-11-18

Windows 分支加固：先备份、再写入、断开精确还原；并补上 SOCKS4 预检。

- **Windows 兼容模式（默认开启）**：WinINet 只支持 SOCKS4，且要求在本地解析域名，
  被污染的域名会被解析成错误 IP。现在连接 SOCKS5 时会在本机 `127.0.0.1` 启动一个
  HTTP→SOCKS5 转换器，系统代理写成 `http=127.0.0.1:端口`；HTTPS 走 CONNECT，把域名
  交给上游解析。实测系统层可正常打开 x.com / google.com。断开时自动停止转换器；
  设置环境变量 `NETPUFF_NO_BRIDGE=1` 可退回纯 SOCKS4 模式。
- **系统代理备份/还原**：写入前把 `ProxyEnable / ProxyServer / ProxyOverride /
  AutoConfigURL` 与 8 个代理环境变量快照到 `~/.netpuff_win_state.json`；断开时只还原
  「仍然是我们写入的值」，期间被用户改过的项保留现状并提示。没有快照时只关闭开关，
  **绝不猜用户原来的地址**。
- **SOCKS4 预检**：Windows 系统层（WinINet）只会发 SOCKS4 握手，PAC 里写 SOCKS5 会被
  忽略并退成直连。因此写注册表前先用 SOCKS4 探一次；不通过则明确报错，并提示可加
  `-t` 只用终端代理。实测服务器同时支持 SOCKS4 时，系统层可正常走代理。
- **ProxyOverride**：默认写入 `<local>` 与内网段（`10.*`、`172.16.*`~`172.31.*`、
  `192.168.*`，因为该字段只认通配符、不认 CIDR），并保留用户已有条目；断开时还原。
- **终端环境变量**：改走 `HKCU\Environment` + `WM_SETTINGCHANGE`，不再用 `setx`
  （无 `SUCCESS:` 噪音、无 1024 字符截断）；8 个变量（含大小写与 `no_proxy`）；
  清理时只删自己写的值，用户原有值会恢复。
- **`-t` 语义**：`connect` 不带 `-t` 时不再清空终端代理，避免误删用户自己的配置。
- **CLI**：端口非法、协议失败不再抛未捕获 traceback；参数错误退出码 2，运行失败 3；
  `status` 在关闭状态下不再打印服务器地址。
- **探测**：按 `Content-Length` 读取响应，避免服务端 keep-alive 导致 15 秒超时。
- **IPv6**：代理地址支持 `[IPv6]:端口`，注册表、历史记录、环境变量均正确加方括号。
- **GUI**：DPI 感知、Windows 字体/主题、成功提示按平台显示、取消按钮初始禁用、
  退出确认框传入父窗口。
- **测试**：新增 `tools/socks45-test-server.py`（SOCKS4/4a/5 测试服务端）与
  `tests/`（12 项；注册表测试写在影子键里，不碰用户真实配置）。
- **发行**：新增 Windows 单文件 exe 与 Inno Setup 安装包（按用户安装，无需管理员、
  无需 Python）；macOS `.app` 与窗口统一使用新图标；新增 `windows-build.yml`，
  推 `v*` tag 时自动构建并附加到 Release。

---

## [1.1.0] — 2026-10-30

新增「退出保护」与「启动自动识别」——避免把代理留在系统里却不知道。

- **退出保护**：系统代理仍开启时关闭窗口，会弹出**系统级**对话框询问
  「恢复直连并退出」/「仅退出软件」/「取消」。选「恢复直连并退出」会先清掉
  系统代理与终端代理再退出；若代理已经关掉，则不再弹窗打扰。
  macOS 上同时接管 Cmd+Q，否则用快捷键退出会绕过确认。
- **启动自动识别**：打开软件时自动扫描系统代理配置。若发现仍在代理，直接把
  状态栏切到「⚠ 正在代理」，回填检测到的地址，并异步探测出口地理位置；
  下方「取消代理 / 恢复直连」按钮即可一键关闭。这正是
  「上次选了仅退出、过段时间想把代理关掉」的场景。
- 关闭判定以**真实系统状态**为准（而非内存里的状态位），因此在软件之外手动
  开关代理也能被正确识别。
- 状态栏文本增加截断保护，避免过长提示被无声裁切。
- 新增 `get_proxy_detail()`：读取系统代理的协议 / 地址 / 端口，供启动识别与
  出口探测使用（Windows 侧解析 `ProxyServer` 的多协议映射，按
  socks > http > https 取优先级）。
- 修复：macOS 原生对话框脚本曾误用 `with icon caution`（那是 `display dialog`
  的参数），导致 `display alert` 编译失败；已改为 `as warning`。

---

## [1.0.2] — 2026-10-15

修复 Windows 输出编码导致的崩溃，并把 CI 拆分为独立工作流。

- **修复**：Windows 上控制台或「被重定向的输出」编码通常不是 UTF-8
  （如 CP1252 / CP936），此前 `print` 中文会抛 `UnicodeEncodeError`
  直接导致 CLI 崩溃（例如 `python netpuff.py status > out.txt`）。
  现在启动时统一把 stdout / stderr 切到 UTF-8，并把无法编码的字符替换掉。
- 新增 `ci.yml`：推 main 或提 PR 时在 **macOS 与 Windows 两个平台**运行冒烟检查
  （语法、版本号一致性、CLI、协议端到端、`.bat` 行尾）。Windows 步骤统一使用
  bash，避免 PowerShell 引号转义与编码差异造成的「步骤全挂但代码没问题」。
- `release.yml` 精简为只负责打 tag 时的构建与发布，Windows 检查移入 `ci.yml`。

---

## [1.0.1] — 2026-10-15

发行工程与文档改进（**程序功能无变化**）。

- 新增 macOS **`.dmg`** 发行包（此前仅提供 `.zip`），更符合 macOS 安装习惯：
  内含 `NetPuff.app` 与指向 `/Applications` 的快捷方式
- 新增 **Windows 发行包**：**功能尚未完善，不建议日常使用**。提供该包的用途是让
  贡献者可以直接解压运行、修改并提交改动（详见包内 `README-Windows.txt`）
- 发行说明扩充为 macOS / Windows 双平台、中英对照，并明确标注 Windows 为未完善状态
- README 新增「质量验证」章节，记录可复现的验证方法与实测结果
- 新增 Windows 冒烟检查（语法、CLI、注册表读取路径、`.bat` 行尾），**不阻塞发布**

---

## [1.0.0] — 2026-10-14

首个正式版。

- 跨平台系统代理切换（macOS / Windows），GUI + 命令行双入口
- 支持三种代理协议：SOCKS5 / HTTP / HTTPS
- macOS：`networksetup` 设置系统代理，自动识别当前网络服务（Wi-Fi / 有线）
- Windows：注册表 `Internet Settings` + Wininet 刷新
- 终端代理：向 shell rc（macOS）或用户环境变量（Windows）写入
  `http_proxy / https_proxy / all_proxy`，并带内网 `no_proxy` 白名单
- 连接前先「探针」验证代理可用，再写系统配置，避免设成死地址
- 通过代理查询出口 IP / 地理位置 / 延迟，直连时也能查本机真实出口
- 历史连接 IP 自动记忆（`~/.netpuff_history.json`）
- 手写 SOCKS5 协议（RFC 1928，无认证 + 域名转发），零第三方依赖
- 许可证：MIT
