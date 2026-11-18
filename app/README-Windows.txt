NetPuff — Windows 版说明（v1.2.0）
==================================

安装包与便携版不需要安装 Python。

功能
----
* 一键连接 / 断开，支持 SOCKS5 / HTTP；连接前先探测出口（IP、国家、城市、ISP、延迟）。
* **兼容模式（默认开启）**：Windows 系统代理只认 SOCKS4，且要求在本地解析域名；
  NetPuff 在本机 127.0.0.1 起一个 HTTP→SOCKS5 转换器，系统代理指向本机，
  域名交给上游解析——被墙站点（x.com、google.com 等）也能打开。
  只监听本机回环，断开时自动停止；`NETPUFF_NO_BRIDGE=1` 可关闭（退回纯 SOCKS4）。
* 写入前备份注册表四项与 8 个环境变量；断开时只还原仍属于 NetPuff 的值，
  期间被用户改过的项保留并提示。没有备份时只关开关，绝不猜用户原来的地址。
* 退出保护：代理仍开启时关闭窗口会弹系统对话框（恢复直连 / 仅退出 / 取消）。
* 启动自检：打开即检测系统代理，回填地址并显示当前出口。
* 内网直连：自动写入 ProxyOverride（<local> 与 10/172.16-31/192.168 网段）。
* 终端代理：写 8 个环境变量（含 no_proxy），只清理自己写入且未被改动的值。

安装
----
推荐：双击 NetPuff-1.2.0-Setup.exe（按用户安装，无需管理员，自动建开始菜单快捷方式）。
便携：双击 NetPuff.exe，无需安装。
从源码：需要 Python 3.10+，双击 app\start-netpuff.bat。

使用
----
安装版：从开始菜单或桌面启动 NetPuff。
便携版：双击 NetPuff.exe。
源码运行：双击 app\start-netpuff.bat（需要 Python）。

填服务器 IP / 端口 → 协议选 socks5 → 「连接代理」；
成功后状态栏显示出口国家与城市；「取消代理 / 恢复直连」恢复。

命令行（源码版）：
    python src\netpuff.py status                 查看系统代理状态
    python src\netpuff.py test  <IP> [端口]       只测试代理，不改系统设置
    python src\netpuff.py connect <IP> [端口] [-t] 测试并开启系统代理
    python src\netpuff.py disconnect             恢复直连
    python src\netpuff.py direct                 查看本机直连出口 IP

已知限制
--------
1. 系统代理只影响遵循 IE / WinINet 设置的程序（Chrome / Edge 会；Firefox 默认不跟随；
   部分原生程序不遵循）。这是 Windows 平台的固有局限，不是本程序 bug。
2. `-p https` 在 Windows 不支持：WinINet 没有「TLS 连代理」概念，请用 socks5 或 http。
3. 终端代理只对**新开的**终端生效，已打开的终端不会自动重读环境变量。
4. 安装包与 exe 未做代码签名，SmartScreen 可能提示「未知发布者」；
   点「更多信息 → 仍要运行」即可。
5. 兼容模式会在本机回环内转发（127.0.0.1），不经过第三方。

排错
----
* 端口未开放：代理服务没启动或 IP 变了，先 `test <IP>`。
* 换网络后连不上：内网代理 IP 会变，更新为当前网段的地址。
* 浏览器打不开被墙站点：确认兼容模式未被 `NETPUFF_NO_BRIDGE=1` 关闭；
  少数程序不遵循系统代理，需要单独配置。
* 关掉软件后代理还开着：退出时选了「仅退出软件」。重新打开会自动识别，
  点「取消代理 / 恢复直连」即可。

参与贡献
--------
仓库：https://github.com/hengjunguo35-oss/NetPuff
问题反馈请附：Windows 版本、是否为安装版/便携版、复现步骤与完整报错。

本程序不提供代理服务、不中转第三方流量、不内置任何节点；
它连接的是你自己提供的代理服务器。仅供合法用途，详见 LICENSE（MIT）与免责声明。

================================================================================
NetPuff — Windows build (v1.2.0)
================================================================================
No Python runtime is required for the installer or the portable exe.

Features
--------
* One-click connect/disconnect with SOCKS5 or HTTP, egress probe before applying.
* Compatibility mode (on by default): Windows only speaks SOCKS4 and resolves DNS
  locally, so blocked domains fail. NetPuff runs a local HTTP→SOCKS5 bridge on
  127.0.0.1; the system proxy points to it and the upstream resolves host names.
  Loopback only, stopped on disconnect; disable with NETPUFF_NO_BRIDGE=1.
* Snapshot before writing: four registry values and eight environment variables are
  restored exactly on disconnect; values changed by the user are preserved.
* Quit protection, startup self-check, ProxyOverride for private ranges, and a
  terminal proxy that only removes the variables it wrote.

Install
-------
Recommended: NetPuff-1.2.0-Setup.exe (per-user, no admin, Start Menu shortcut).
Portable: NetPuff.exe, double-click to run.
From source: Python 3.10+, double-click app\start-netpuff.bat.

Known limitations
-----------------
1. Only programs that follow IE/WinINet settings are affected (Chrome/Edge do;
   Firefox does not by default).
2. `-p https` is unsupported on Windows (no TLS-to-proxy concept in WinINet).
3. Terminal proxy only affects newly opened terminals.
4. Unsigned build: SmartScreen may warn; choose "More info → Run anyway".
5. Compatibility mode relays locally on 127.0.0.1 only.

Repository: https://github.com/hengjunguo35-oss/NetPuff
This program provides no proxy service and bundles no nodes; you connect to your own
proxy server. For lawful use only. See LICENSE (MIT) and the disclaimer.
