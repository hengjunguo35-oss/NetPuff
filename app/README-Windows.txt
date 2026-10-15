NetPuff — Windows 版说明
=========================

⚠️  功能尚未完善，不建议日常使用。

为什么仍然提供这个包？
----------------------
为了让开发者能够直接解压、运行、修改并提交贡献。
Windows 相关代码集中在 src/netpuff.py 的 IS_WIN 分支：

    set_system_proxy()      / clear_system_proxy()
    set_terminal_proxy()    / clear_terminal_proxy()
    get_proxy_status()
    _win_refresh()          （ctypes 调 Wininet 的 InternetSetOption）

启动脚本：app/start-netpuff.bat
（包内使用 ASCII 文件名，以规避 Windows 上 zip 中文名的编码问题；
  仓库中对应 app/启动NetPuff.bat，内容完全相同）

已知问题
--------
1. Windows 分支（注册表 Internet Settings + Wininet 刷新 + setx 环境变量）
   未经充分实机验证，可能存在兼容性问题。
2. 系统 SOCKS 代理依赖 IE 设置：只有遵循系统代理的程序才会生效
   （Chrome / Edge 会；Firefox 默认不跟随；部分原生程序不遵循）。
   这是 Windows 平台的固有局限，不是本程序的 bug。
3. 终端代理只对「新开的」终端生效，已打开的终端不会自动重读环境变量。

运行前提
--------
* 已安装 Python 3（3.10 / 3.11 / 3.12），安装时务必勾选
  "Add python.exe to PATH"。
* 零第三方依赖：只用 Python 标准库；tkinter 需随 Python 一并安装
  （python.org 的官方安装包默认包含）。

使用
----
双击    app\start-netpuff.bat

或命令行：
    python src\netpuff.py status                 查看系统代理状态
    python src\netpuff.py test  <IP> [端口]       只测试代理，不改系统设置
    python src\netpuff.py connect <IP> [端口] [-t] 测试并开启系统代理
    python src\netpuff.py disconnect             恢复直连
    python src\netpuff.py direct                 查看本机直连出口 IP

参与贡献
--------
仓库：https://github.com/hengjunguo35-oss/NetPuff

发现 bug 或有改进想法，欢迎开 Issue，并请附上：
  * Windows 版本（如 Windows 11 23H2）
  * Python 版本（python --version）
  * 复现步骤与实际现象（含完整报错信息）

本项目不提供代理服务、不承载任何流量、不内置任何节点；
它连接的是你自己提供的代理服务器。仅供合法用途，请遵守当地法律法规。
详见仓库中的 LICENSE（MIT）与免责声明。


================================================================================
NetPuff — Windows build
================================================================================

⚠️  NOT yet complete — not recommended for daily use.

Why is this package provided?
-----------------------------
So that developers can unzip it, run it, patch it, and submit changes.
The Windows-specific code lives in the IS_WIN branches of src/netpuff.py:

    set_system_proxy()      / clear_system_proxy()
    set_terminal_proxy()    / clear_terminal_proxy()
    get_proxy_status()
    _win_refresh()          (calls Wininet InternetSetOption via ctypes)

Launcher: app/start-netpuff.bat
(An ASCII filename is used inside the package to avoid zip filename-encoding problems on
 Windows. The equivalent file in the repository is app/启动NetPuff.bat — identical contents.)

Known issues
------------
1. The Windows branch (registry Internet Settings + Wininet refresh + setx env vars) has
   not been fully verified on real hardware and may have compatibility issues.
2. System SOCKS relies on IE settings: only programs that follow the system proxy are
   affected (Chrome / Edge do; Firefox does not by default; some native apps do not).
   This is an inherent Windows-platform limitation, not a bug in this program.
3. The terminal proxy only affects *newly opened* terminals; already-open ones will not
   re-read the environment variables.

Requirements
------------
* Python 3 installed (3.10 / 3.11 / 3.12), with "Add python.exe to PATH" ticked
  during installation.
* Zero third-party dependencies: Python standard library only. tkinter must be present
  (the official python.org installer includes it by default).

Usage
-----
Double-click   app\start-netpuff.bat

Or from the command line:
    python src\netpuff.py status                   show system proxy state
    python src\netpuff.py test  <IP> [port]        test the proxy only
    python src\netpuff.py connect <IP> [port] [-t] test and enable the system proxy
    python src\netpuff.py disconnect               restore direct connection
    python src\netpuff.py direct                   show your real direct egress IP

Contributing
------------
Repository: https://github.com/hengjunguo35-oss/NetPuff

Bug reports and ideas are welcome — please open an Issue and include:
  * your Windows version (e.g. Windows 11 23H2)
  * your Python version (`python --version`)
  * reproduction steps and the actual behaviour, including the full error output

This program provides no proxy service, carries no traffic, and bundles no nodes; it
connects to a proxy server that you supply yourself. For lawful use only — please comply
with the laws of your country/region. See LICENSE (MIT) and the disclaimer in the repository.
