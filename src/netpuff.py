#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  NetPuff / netpuff.py — 跨平台系统代理切换器（macOS / Windows）
# ============================================================================
#
#  ── 一句话原理 ─────────────────────────────────────────────────────────────
#
#  代理切换器本身**不承载任何流量转发**，它只做两件事：
#    ① 替你把「代理服务器地址」写进操作系统/终端的环境里；
#    ② 通过代理服务器发起一次真实的 HTTP 请求，验证这条链路确实可用，
#       并把出口 IP 和地理位置显示出来。
#
#  真正的网络出口由那台 SOCKS5 服务器（通常是 10.x / 192.168.x 内网机器）
#  提供。本程序是一个「开关 + 探针」，负责在直连和代理之间来回切换，
#  并让你一眼确认现在到底走没走通、出口在哪。
#
#  ── 完整功能结构 ───────────────────────────────────────────────────────────
#
#   ┌─────────────┐     手动填 IP/端口      ┌──────────────────────┐
#   │  GUI (Tk)   │ ─────────────────────▶ │  fetch_exit_info()   │  ← 探针：走代理查出口
#   │  或 CLI     │  后台线程 + queue 回传   └──────────┬───────────┘
#   └─────────────┘                                     │ 通了
#                                             ┌─────────▼───────────┐
#                                             │ set_system_proxy()  │  ← 写系统代理
#                                             │ set_terminal_proxy()│  ← 写终端环境变量
#                                             └─────────────────────┘
#   取消时反向：clear_system_proxy() + clear_terminal_proxy() 恢复直连。
#
#  ── ★ 最关键的一个技术点：SOCKS5 协议要自己实现 ───────────────────────────
#
#  Python 标准库的 urllib 只认 http_proxy / https_proxy，不认识 socks 代理。
#  为了不引入第三方依赖，程序用裸 socket 手写了 SOCKS5 握手（见
#  socks5_http_get()），流程是：
#     握手(无认证) → CONNECT 目标主机 → 服务器返回其出口地址 → 再发真实 HTTP。
#
#  ── 跨平台怎么做到的 ───────────────────────────────────────────────────────
#
#  macOS   用 `networksetup` 改系统 SOCKS/HTTP 代理（要先把「网络接口」映射成
#          「网络服务名」，见 mac_primary_service()）。
#  Windows 用注册表 HKCU\...\Internet Settings 写 ProxyEnable/ProxyServer，
#          再用 Wininet 的两个 InternetSetOption 通知系统刷新。
#  终端代理  往 shell 的 rc 文件（macOS）或用户环境变量（Windows）里写
#          http_proxy/https_proxy/all_proxy。
#
#  ── 依赖 ───────────────────────────────────────────────────────────────────
#
#  仅 Python 标准库（tkinter / socket / ssl / subprocess / winreg 等），
#  零第三方依赖。GUI 用 tkinter；网络探测用裸 socket。
#
#  ── 使用 ───────────────────────────────────────────────────────────────────
#
#    GUI：  python3 netpuff.py（无参数即启动图形界面）
#    CLI：  python3 netpuff.py status | test <IP> [端口] [-p 协议]
#           python3 netpuff.py connect <IP> [端口] [-t]
#           python3 netpuff.py disconnect | direct
#
# ============================================================================


import json
import os
import platform
import queue
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")

APP_TITLE = "NetPuff"
APP_VERSION = "1.0.1"          # 唯一版本来源（与 CHANGELOG.md 保持一致）
USER_AGENT = "%s/%s" % (APP_TITLE, APP_VERSION)
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".netpuff_history.json")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".netpuff_config.json")
DEFAULT_PORT = "2080"
GEO_API = "http://ip-api.com/json/?fields=status,country,regionName,city,isp,timezone,query&lang=zh-CN"
PROTOCOLS = ("socks5", "http", "https")

PY = sys.executable


# ======================================================================
# 历史记录
# ======================================================================
def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_history(entries):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def add_history(ip, port):
    entries = load_history()
    entries = [e for e in entries
               if e.get("ip") != ip or str(e.get("port")) != str(port)]
    entries.insert(0, {"ip": ip, "port": str(port),
                       "last_used": time.strftime("%Y-%m-%d %H:%M")})
    entries = entries[:20]
    save_history(entries)
    return entries


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ======================================================================
# 基础网络工具
# ======================================================================
def _recv_exact(s, n):
    data = b""
    while len(data) < n:
        chunk = s.recv(n - len(data))
        if not chunk:
            raise ConnectionError("连接被对端关闭")
        data += chunk
    return data


def _read_http_body(s):
    data = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
    return data.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in data else data


def socks5_http_get(proxy_host, proxy_port, url, timeout=15):
    """通过 SOCKS5 代理（无认证）发起一次 HTTP(S) GET，返回响应正文文本。

    为什么不用 urllib 直接设 socks 代理？
    Python 标准库的 urllib 只认 http_proxy/https_proxy，不支持 socks5h://。
    为了零第三方依赖，这里用裸 socket 手写了 SOCKS5（RFC 1928）握手。
    之所以不用「本地 DNS 解析 + 发 IP」的形式，而是把**域名**发给代理
    （atyp=0x03），是为了让代理服务器那端去解析域名——这能绕开本地 DNS
    污染，跟 curl 的 socks5h:// 语义一致。

    SOCKS5 无认证握手分三步，各字段含义见下方行内注释。
    """
    u = urllib.parse.urlparse(url)
    use_ssl = u.scheme == "https"
    target_host = u.hostname
    target_port = u.port or (443 if use_ssl else 80)

    s = socket.create_connection((proxy_host, int(proxy_port)), timeout=timeout)
    s.settimeout(timeout)
    try:
        # ① 问候：VER=0x05(SOCKS5) NMETHODS=1 METHODS=[0x00 无认证]
        s.sendall(b"\x05\x01\x00")
        if _recv_exact(s, 2) != b"\x05\x00":
            # 服务器回复 VER=0x05 METHOD=0x00 表示同意无认证
            raise ConnectionError("SOCKS5 需要认证或协议不受支持")

        hb = target_host.encode("utf-8")
        # ② CONNECT 请求：VER=0x05 CMD=0x01(CONNECT) RSV=0x00
        #    ATYP=0x03(域名) 域名长度 域名 目标端口(大端 2 字节)
        req = b"\x05\x01\x00\x03" + bytes([len(hb)]) + hb + target_port.to_bytes(2, "big")
        s.sendall(req)
        head = _recv_exact(s, 4)  # VER REP RSV ATYP
        if head[1] != 0x00:       # REP=0x00 才表示连接成功
            raise ConnectionError("SOCKS5 连接被拒绝 (code=%d)" % head[1])
        # ③ 跳过服务器回填的「绑定地址」：可能是 IPv4(4) / 域名(变长) / IPv6(16)
        atyp = head[3]
        if atyp == 0x01:
            _recv_exact(s, 4)
        elif atyp == 0x03:
            _recv_exact(s, _recv_exact(s, 1)[0])
        elif atyp == 0x04:
            _recv_exact(s, 16)
        else:
            raise ConnectionError("SOCKS5 响应格式错误")
        _recv_exact(s, 2)  # 绑定端口（丢弃，用不到）

        if use_ssl:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=target_host)

        path = u.path or "/"
        if u.query:
            path += "?" + u.query
        req = ("GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: %s\r\n"
               "Accept: */*\r\nConnection: close\r\n\r\n" % (path, target_host, USER_AGENT))
        s.sendall(req.encode("utf-8"))
        return _read_http_body(s).decode("utf-8", "replace")
    finally:
        try:
            s.close()
        except Exception:
            pass


def http_proxy_get(proxy_host, proxy_port, url, secure=False, timeout=15):
    """通过 HTTP/HTTPS 代理（绝对 URI 形式）发起 GET，返回正文文本。

    与 SOCKS5 不同，HTTP 代理不认识「域名 + 端口」这种目标描述，
    它的协议就是「把完整 URL 直接写在请求行里」：
        GET http://example.com/path HTTP/1.1
    代理服务器看到绝对 URI 就会代为转发。HTTPS 代理则先和代理服务器
    建立 TLS（CONNECT 隧道语义由服务器处理），这里用 secure 参数区分。
    """
    u = urllib.parse.urlparse(url)
    target_host = u.hostname

    s = socket.create_connection((proxy_host, int(proxy_port)), timeout=timeout)
    s.settimeout(timeout)
    try:
        if secure:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=proxy_host)

        req = ("GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: %s\r\n"
               "Accept: */*\r\nConnection: close\r\n\r\n" % (url, target_host, USER_AGENT))
        s.sendall(req.encode("utf-8"))
        return _read_http_body(s).decode("utf-8", "replace")
    finally:
        try:
            s.close()
        except Exception:
            pass


def direct_http_get(url, timeout=10):
    """直连（不走任何代理）发起 GET，返回正文文本。

    用途：取消代理后，向用户展示「本机真实出口 IP / 地理位置」，
    让用户确认已经回到了直连状态，而不是还在偷偷走代理。
    实现上就是最朴素的 socket 直连目标主机，不经过任何代理。
    """
    u = urllib.parse.urlparse(url)
    host = u.hostname
    port = u.port or (443 if u.scheme == "https" else 80)

    s = socket.create_connection((host, port), timeout=timeout)
    s.settimeout(timeout)
    try:
        if u.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=host)
        path = u.path or "/"
        if u.query:
            path += "?" + u.query
        req = ("GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: %s\r\n"
               "Accept: */*\r\nConnection: close\r\n\r\n" % (path, host, USER_AGENT))
        s.sendall(req.encode("utf-8"))
        return _read_http_body(s).decode("utf-8", "replace")
    finally:
        try:
            s.close()
        except Exception:
            pass


def check_port_open(host, port, timeout=3):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def _parse_geo_json(body):
    info = json.loads(body)
    if info.get("status") != "success":
        raise ConnectionError("地理位置查询失败：%s" % info.get("message", "未知错误"))
    return {
        "ip": info.get("query", ""),
        "country": info.get("country", ""),
        "region": info.get("regionName", ""),
        "city": info.get("city", ""),
        "isp": info.get("isp", ""),
        "timezone": info.get("timezone", ""),
    }


def fetch_exit_info(host, port, scheme="socks5"):
    """通过代理查询出口 IP 与地理位置。失败抛异常。

    这是整个程序的「探针」核心：调用 GEO_API（ip-api.com），
    由代理服务器代为访问，从而拿到**代理出口**的 IP 与地理位置。
    顺带测出代理链路延迟（从发起到拿到完整响应的时间）。

    注意：这里故意用「裸协议 + 明文 HTTP 查询」，而不是走系统代理，
    因为此时系统代理可能还没设上——探针必须先于「设置系统代理」完成，
    确认代理真的可用后再写系统配置，避免把系统代理设成一个死地址。
    """
    start = time.time()
    if scheme == "socks5":
        body = socks5_http_get(host, port, GEO_API, timeout=15)
    elif scheme in ("http", "https"):
        body = http_proxy_get(host, port, GEO_API, secure=(scheme == "https"), timeout=15)
    else:
        raise ValueError("未知协议: %s" % scheme)
    latency = round((time.time() - start) * 1000)
    info = _parse_geo_json(body)
    info["latency_ms"] = latency
    info["scheme"] = scheme
    return info


def fetch_direct_exit_info():
    """直连查询本机出口 IP 与地理位置（用于取消代理后展示）。"""
    body = direct_http_get(GEO_API, timeout=10)
    return _parse_geo_json(body)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "未知"


def notify(title, msg):
    """系统通知（macOS 用通知中心，Windows 暂静默）。"""
    if IS_MAC:
        try:
            subprocess.run(["osascript", "-e",
                            'display notification "%s" with title "%s"' % (msg, title)],
                           check=False)
        except Exception:
            pass


# ======================================================================
# 系统代理设置（平台相关）
# ======================================================================
def mac_primary_service():
    """找出「当前在用的」macOS 网络服务名。

    为什么要这个函数？
    networksetup 设代理时要求传「网络服务名」（如 "Wi-Fi"、"Ethernet"），
    而不是网络接口名（如 en0）也不是 IP。但系统可能同时有 Wi-Fi、雷雳、
    USB 网卡等多个服务，直接写死 "Wi-Fi" 在插网线的机器上会设错地方。

    做法：先查默认路由走哪个接口（`route get default` 的 interface 字段），
    再反查 `networksetup -listallhardwareports` 里该接口对应的服务名。
    找不到就退回 "Wi-Fi" 兜底（绝大多数情况是对的）。
    """
    try:
        r = subprocess.run(["route", "-n", "get", "default"],
                           capture_output=True, text=True)
        iface = None
        for line in r.stdout.splitlines():
            if line.strip().startswith("interface:"):
                iface = line.split(":", 1)[1].strip()
        if iface:
            hw = subprocess.run(["networksetup", "-listallhardwareports"],
                                capture_output=True, text=True)
            cur = None
            for line in hw.stdout.splitlines():
                if line.startswith("Hardware Port:"):
                    cur = line.split(":", 1)[1].strip()
                elif line.startswith("Device:") and line.split(":", 1)[1].strip() == iface:
                    return cur
    except Exception:
        pass
    return "Wi-Fi"


def set_system_proxy(host, port, scheme="socks5"):
    """把系统级代理写进操作系统。这是跨平台分叉的核心之一。

    macOS   ：调 networksetup，按协议分别用
             -setsocksfirewallproxy / -setwebproxy / -setsecurewebproxy，
             再单独用 -set…proxystate on 打开开关（地址与开关是两个命令）。
    Windows ：写注册表 HKCU\\Software\\Microsoft\\Windows\\CurrentVersion
             \\Internet Settings，ProxyEnable=1、ProxyServer="socks=ip:port"，
             写完调 _win_refresh() 让 Wininet 立即生效。

    一个关键区别：macOS 的 SOCKS 代理是全局的（几乎对所有 App 生效）；
    Windows 的这套「IE 设置」只对遵循系统代理的程序生效（Chrome/Edge 会，
    部分程序不会）——这是 Windows 平台固有的局限，见技术文档「已知限制」。
    """
    if scheme not in PROTOCOLS:
        raise ValueError("未知协议: %s" % scheme)

    if IS_MAC:
        svc = mac_primary_service()
        if scheme == "socks5":
            subprocess.run(["networksetup", "-setsocksfirewallproxy", svc, host, str(port)], check=True)
            subprocess.run(["networksetup", "-setsocksfirewallproxystate", svc, "on"], check=True)
        elif scheme == "http":
            subprocess.run(["networksetup", "-setwebproxy", svc, host, str(port)], check=True)
            subprocess.run(["networksetup", "-setwebproxystate", svc, "on"], check=True)
        else:  # https
            subprocess.run(["networksetup", "-setsecurewebproxy", svc, host, str(port)], check=True)
            subprocess.run(["networksetup", "-setsecurewebproxystate", svc, "on"], check=True)
        return "macOS · %s · %s" % (svc, scheme.upper())

    elif IS_WIN:
        import winreg
        tag = {"socks5": "socks", "http": "http", "https": "https"}[scheme]
        path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ,
                          "%s=%s:%s" % (tag, host, port))
        winreg.CloseKey(key)
        _win_refresh()
        return "Windows · %s" % scheme.upper()

    else:
        raise NotImplementedError("暂不支持当前系统")


def clear_system_proxy():
    if IS_MAC:
        svc = mac_primary_service()
        for args in (["-setsocksfirewallproxystate", svc, "off"],
                     ["-setwebproxystate", svc, "off"],
                     ["-setsecurewebproxystate", svc, "off"]):
            subprocess.run(["networksetup"] + args, check=False)
        return "macOS · 网络服务 %s" % svc
    elif IS_WIN:
        import winreg
        path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        _win_refresh()
        return "Windows · 注册表"
    else:
        raise NotImplementedError("暂不支持当前系统")


def get_proxy_status():
    """查询系统代理状态，返回 (是否有任一代理开启, 服务器地址描述)。

    macOS 上 SOCKS / HTTP / HTTPS 是三个互相独立的开关。本工具三种协议都支持
    设置，所以查询时也必须三个都看——只查 SOCKS 的话，用 `-p http` 连上之后
    状态会误报「关闭」，让用户以为没生效。
    """
    if IS_MAC:
        svc = mac_primary_service()
        enabled = False
        servers = []
        for flag in ("-getsocksfirewallproxy", "-getwebproxy",
                     "-getsecurewebproxy"):
            r = subprocess.run(["networksetup", flag, svc],
                               capture_output=True, text=True).stdout
            if "Enabled: Yes" in r:
                enabled = True
            for line in r.splitlines():
                if line.startswith("Server:"):
                    addr = line.split(":", 1)[1].strip()
                    if addr and addr not in servers:
                        servers.append(addr)
                    break
        return (enabled, " / ".join(servers))
    elif IS_WIN:
        import winreg
        path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        enabled = False
        server = ""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ)
            try:
                enabled = bool(winreg.QueryValueEx(key, "ProxyEnable")[0])
                server = winreg.QueryValueEx(key, "ProxyServer")[0] or ""
            finally:
                winreg.CloseKey(key)
        except OSError:
            # 注册表键或值不存在（例如全新的用户配置）——按「未开启」处理，
            # 不要让 `status` 直接抛异常崩掉。
            pass
        return (enabled, server)
    return (False, "")


def _win_refresh():
    """通知 Windows 的 Wininet「代理设置变了，立即刷新」。

    只改注册表，正在运行的浏览器/程序不会主动重读，必须通过
    InternetSetOption 广播两个事件：
      39 = INTERNET_OPTION_SETTINGS_CHANGED  让系统重新读注册表
      37 = INTERNET_OPTION_REFRESH           让已建立的连接按新代理重连
    这两个是 Wininet 里众所周知的魔法数字（MSDN 未给具名常量），
    所以这里直接用数字并注明含义，避免后人不明所以。
    """
    try:
        import ctypes
        ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
    except Exception:
        pass


# ======================================================================
# 终端代理（写入 shell 配置 / Windows 用户环境变量）
# ======================================================================
SHELL_RC = os.path.expanduser("~/.zshrc")
MARKER_START = "# >>> NetPuff 终端代理 >>>"
MARKER_END = "# <<< NetPuff 终端代理 <<<"
NO_PROXY = "localhost,127.0.0.1,::1,10.0.0.0/8,192.168.0.0/16,172.16.0.0/12"


def _proxy_url(scheme, host, port):
    if scheme == "socks5":
        return "socks5h://%s:%s" % (host, port)
    return "http://%s:%s" % (host, port)  # http/https 代理在环境变量里都写 http://


def _strip_marked_block(content):
    lines = content.split("\n")
    out = []
    inside = False
    for line in lines:
        s = line.strip()
        if s == MARKER_START:
            inside = True
            continue
        if s == MARKER_END:
            inside = False
            continue
        if not inside:
            out.append(line)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def set_terminal_proxy(host, port, scheme="socks5"):
    """把代理写进 shell 配置（macOS）或用户环境变量（Windows）。

    系统代理只管浏览器等 GUI 程序；命令行工具（curl/pip/git 等）只认
    环境变量 http_proxy/https_proxy/all_proxy。所以要「两处都设」，
    终端里的工具才能真正走代理。

    设计上用了「标记块」：写入的内容夹在一对 MARKER 注释之间，
    取消时按标记精确删除，绝不误删用户 .zshrc 里已有的其他配置。
    同时写大写 + 小写两套变量，因为不同工具认的大小写不同（curl 认小写，
    部分老程序只认大写），干脆都设上。

    no_proxy 白名单排除内网段（10.x/192.168.x/172.16.x），
    否则访问内网服务也会被送进代理——这是常见的坑。
    """
    url = _proxy_url(scheme, host, port)
    block = ("%s\n"
             "export http_proxy=\"%s\"\n"
             "export https_proxy=\"%s\"\n"
             "export all_proxy=\"%s\"\n"
             "export HTTP_PROXY=\"$http_proxy\"\n"
             "export HTTPS_PROXY=\"$https_proxy\"\n"
             "export ALL_PROXY=\"$all_proxy\"\n"
             "export no_proxy=\"%s\"\n"
             "export NO_PROXY=\"$no_proxy\"\n"
             "%s\n") % (MARKER_START, url, url, url, NO_PROXY, MARKER_END)

    if IS_MAC:
        path = SHELL_RC
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = ""
        content = _strip_marked_block(content)
        if content and not content.endswith("\n"):
            content += "\n"
        content += "\n" + block
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
    elif IS_WIN:
        for var in ("http_proxy", "https_proxy", "all_proxy"):
            subprocess.run(["setx", var, url], check=False)
        return "Windows 用户环境变量"
    return ""


def clear_terminal_proxy():
    if IS_MAC:
        path = SHELL_RC
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return path
        content = _strip_marked_block(content)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
    elif IS_WIN:
        for var in ("http_proxy", "https_proxy", "all_proxy"):
            subprocess.run(["setx", var, ""], check=False)
        return "Windows 用户环境变量"
    return ""


# ======================================================================
# 命令行模式（便于无界面验证）
# ======================================================================
def cli():
    import argparse
    p = argparse.ArgumentParser(description=APP_TITLE)
    sub = p.add_subparsers(dest="cmd")

    def add_proto(parser):
        parser.add_argument("-p", "--protocol", default="socks5",
                            choices=list(PROTOCOLS), help="代理协议")

    s_test = sub.add_parser("test", help="测试代理并显示出口信息（不修改系统代理）")
    s_test.add_argument("host")
    s_test.add_argument("port", nargs="?", default=DEFAULT_PORT)
    add_proto(s_test)

    s_conn = sub.add_parser("connect", help="测试并开启系统代理")
    s_conn.add_argument("host")
    s_conn.add_argument("port", nargs="?", default=DEFAULT_PORT)
    s_conn.add_argument("-t", "--terminal", action="store_true", help="同时设置终端代理")
    add_proto(s_conn)

    sub.add_parser("disconnect", help="取消代理，恢复直连")
    sub.add_parser("status", help="查看当前系统代理状态")
    sub.add_parser("direct", help="查看当前直连出口 IP")

    args = p.parse_args()

    if args.cmd == "test":
        print("检测端口 %s:%s (%s) ..." % (args.host, args.port, args.protocol))
        if not check_port_open(args.host, args.port):
            print("✗ 端口未开放（代理服务可能没启动）")
            sys.exit(1)
        print("查询出口信息 ...")
        info = fetch_exit_info(args.host, args.port, args.protocol)
        print("✓ 出口 IP  : %s" % info["ip"])
        print("  地理位置  : %s / %s / %s" % (info["country"], info["region"], info["city"]))
        print("  ISP       : %s" % info["isp"])
        print("  时区       : %s" % info["timezone"])
        print("  延迟       : %d ms" % info["latency_ms"])

    elif args.cmd == "connect":
        if not check_port_open(args.host, args.port):
            print("✗ 端口 %s:%s 未开放" % (args.host, args.port))
            sys.exit(1)
        info = fetch_exit_info(args.host, args.port, args.protocol)
        where = set_system_proxy(args.host, args.port, args.protocol)
        if getattr(args, "terminal", False):
            where2 = set_terminal_proxy(args.host, args.port, args.protocol)
            print("✓ 已开启系统代理（%s）" % where)
            print("✓ 终端代理已写入（%s）" % where2)
        else:
            clear_terminal_proxy()
            print("✓ 已开启系统代理（%s）" % where)
        add_history(args.host, args.port)
        print("  出口 IP : %s（%s / %s / %s）" % (
            info["ip"], info["country"], info["region"], info["city"]))

    elif args.cmd == "disconnect":
        where = clear_system_proxy()
        where2 = clear_terminal_proxy()
        print("✓ 已取消系统代理，恢复直连（%s）" % where)
        print("✓ 已清除终端代理（%s）" % where2)

    elif args.cmd == "direct":
        info = fetch_direct_exit_info()
        print("直连出口 IP : %s" % info["ip"])
        print("地理位置     : %s / %s / %s" % (info["country"], info["region"], info["city"]))

    elif args.cmd == "status":
        enabled, server = get_proxy_status()
        print("系统代理: %s" % ("开启" if enabled else "关闭"))
        if server:
            print("服务器: %s" % server)
    else:
        p.print_help()


# ======================================================================
# 图形界面
# ======================================================================
def build_gui():
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("500x565")
    root.minsize(470, 535)

    state = {"info": None, "working": False, "connecting": False}
    msg_q = queue.Queue()

    style = ttk.Style()
    try:
        style.theme_use("aqua")
    except Exception:
        pass

    pad = dict(padx=12, pady=6)

    # ---- 标题 ----
    tk.Label(root, text="NetPuff", font=("Helvetica", 18, "bold")).pack(pady=(16, 2))
    tk.Label(root, text="跨平台 · macOS / Windows", fg="#888888").pack()

    # ---- 合规提示（中英对照，置顶）----
    # 在界面最上方明示「仅供合法用途」，中英双语各一行，避免任何歧义。
    tk.Label(root,
             text="本软件仅供合法用途，禁止用于任何违法行为\n"
                  "For lawful use only. Use for illegal activity is prohibited.",
             fg="#b03030", font=("Helvetica", 10), justify="center").pack(pady=(8, 0))

    # ---- 表单 ----
    form = ttk.LabelFrame(root, text="代理服务器", padding=12)
    form.pack(fill="x", padx=16, pady=12)

    ttk.Label(form, text="服务器 IP:").grid(row=0, column=0, sticky="w", **pad)
    ip_var = tk.StringVar()
    ip_combo = ttk.Combobox(form, textvariable=ip_var, state="normal")
    ip_combo.grid(row=0, column=1, sticky="ew", **pad)

    ttk.Label(form, text="端口:").grid(row=1, column=0, sticky="w", **pad)
    port_var = tk.StringVar(value=DEFAULT_PORT)
    port_entry = ttk.Entry(form, textvariable=port_var, width=12)
    port_entry.grid(row=1, column=1, sticky="w", **pad)

    ttk.Label(form, text="协议:").grid(row=2, column=0, sticky="w", **pad)
    scheme_var = tk.StringVar(value="socks5")
    scheme_combo = ttk.Combobox(form, textvariable=scheme_var, state="readonly",
                                values=list(PROTOCOLS), width=12)
    scheme_combo.grid(row=2, column=1, sticky="w", **pad)

    terminal_var = tk.BooleanVar(value=bool(load_config().get("terminal_proxy", False)))
    terminal_check = ttk.Checkbutton(form, text="同时设置终端代理（命令行工具也走代理）",
                                     variable=terminal_var)
    terminal_check.grid(row=3, column=0, columnspan=2, sticky="w", **pad)

    form.columnconfigure(1, weight=1)

    def refresh_history():
        entries = load_history()
        ip_combo["values"] = ["%s:%s" % (e.get("ip"), e.get("port")) for e in entries]
        return entries

    def on_history_select(_evt=None):
        val = ip_var.get().strip()
        if ":" in val:
            ip, port = val.rsplit(":", 1)
            ip_var.set(ip.strip())
            port_var.set(port.strip())

    ip_combo.bind("<<ComboboxSelected>>", on_history_select)
    refresh_history()

    # ---- 按钮区 ----
    btns = ttk.Frame(root)
    btns.pack(fill="x", padx=16, pady=(6, 10))

    connect_btn = ttk.Button(btns, text="连接代理")
    connect_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

    detail_btn = ttk.Button(btns, text="查看详情", state="disabled")
    detail_btn.pack(side="left", fill="x", expand=True, padx=6)

    # ---- 状态指示区（替代进度条） ----
    status_box = ttk.LabelFrame(root, text="状态", padding=10)
    status_box.pack(fill="x", padx=16, pady=4)

    status_var = tk.StringVar(value="就绪")
    status_label = tk.Label(status_box, textvariable=status_var, anchor="w",
                            font=("Helvetica", 13), fg="#888888")
    status_label.pack(fill="x")

    # ---- 底部取消按钮 ----
    cancel_btn = ttk.Button(root, text="取消代理 / 恢复直连")
    cancel_btn.pack(fill="x", padx=16, pady=(12, 16))

    ttk.Label(root, text="历史记录保存在 ~/.netpuff_history.json",
              foreground="#aaaaaa").pack(side="bottom", pady=(0, 8))

    # ==================================================================
    def set_status(text, color="#888888"):
        status_var.set(text)
        status_label.config(fg=color)

    def _animate_connect(i=0):
        if not state["connecting"]:
            return
        dots = "." * (i % 4)
        set_status("正在连接" + dots, "#0066cc")
        root.after(300, _animate_connect, i + 1)

    def show_detail(info):
        dlg = tk.Toplevel(root)
        dlg.title("连接详情")
        dlg.geometry("430x380")
        dlg.transient(root)
        lines = [
            ("出口 IP", info["ip"]),
            ("地理位置", "%s · %s · %s" % (info["country"], info["region"], info["city"])),
            ("ISP 运营商", info["isp"]),
            ("时区", info["timezone"]),
            ("连接延迟", "%d ms" % info.get("latency_ms", 0)),
            ("代理协议", info.get("scheme", "socks5").upper()),
            ("本机 IP", get_local_ip()),
        ]
        body = ttk.Frame(dlg, padding=16)
        body.pack(fill="both", expand=True)
        for i, (k, v) in enumerate(lines):
            ttk.Label(body, text=k + "：", foreground="#666666").grid(
                row=i, column=0, sticky="ne", pady=4, padx=(0, 8))
            ttk.Label(body, text=v, wraplength=280, justify="left").grid(
                row=i, column=1, sticky="w", pady=4)
        body.columnconfigure(1, weight=1)
        ttk.Button(dlg, text="关闭", command=dlg.destroy).pack(pady=10)

    def _run_connect(host, port, scheme, terminal):
        # 在后台线程里干网络活，绝不阻塞 Tk 主线程。
        # Tk 的 UI 是单线程的：一旦在主线程里做 socket 连接/等待响应，
        # 窗口会直接卡死（转圈、无响应）。所以网络操作全部丢给 daemon 线程，
        # 结果通过 msg_q 队列传回，再由 _poll()（root.after 定时轮询）回 UI 线程渲染。
        try:
            if not check_port_open(host, port):
                raise ConnectionError("端口 %s 未开放（代理服务可能没启动）" % port)
            info = fetch_exit_info(host, port, scheme)
            where = set_system_proxy(host, port, scheme)
            if terminal:
                set_terminal_proxy(host, port, scheme)
            else:
                clear_terminal_proxy()
            add_history(host, port)
            msg_q.put(("connect_ok", info, where, terminal))
        except Exception as e:
            msg_q.put(("connect_fail", str(e), None, None))

    def _connect_done(info, where, terminal=False):
        state["connecting"] = False
        state["working"] = False
        state["info"] = info
        connect_btn.config(state="normal")
        detail_btn.config(state="normal")
        suffix = " · 终端代理已开启" if terminal else ""
        set_status("✓ 已连接 · 出口 %s · %s%s" % (info["country"], info["city"], suffix), "#1a8f3c")
        note = "\n终端代理已写入 ~/.zshrc（新终端生效）" if terminal else ""
        notify("代理连接成功", "出口 IP %s（%s / %s）%s" % (
            info["ip"], info["country"], info["city"], note))

    def _connect_fail(msg):
        state["connecting"] = False
        state["working"] = False
        connect_btn.config(state="normal")
        set_status("✗ 连接失败：%s" % msg, "#cc0000")
        notify("代理连接失败", msg)

    def on_connect():
        host = ip_var.get().strip()
        port = port_var.get().strip()
        scheme = scheme_var.get().strip() or "socks5"
        terminal = terminal_var.get()
        save_config({"terminal_proxy": terminal})
        if not host:
            set_status("✗ 请填写服务器 IP", "#cc0000")
            return
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            set_status("✗ 端口无效（1~65535）", "#cc0000")
            return
        if state["working"]:
            return
        state["working"] = True
        state["connecting"] = True
        connect_btn.config(state="disabled")
        detail_btn.config(state="disabled")
        refresh_history()
        _animate_connect()
        threading.Thread(target=_run_connect, args=(host, port, scheme, terminal), daemon=True).start()

    def on_detail():
        if state["info"]:
            show_detail(state["info"])

    def _run_cancel():
        try:
            where = clear_system_proxy()
            clear_terminal_proxy()
            try:
                info = fetch_direct_exit_info()
                summary = "出口 %s · %s" % (info["country"], info["city"])
                direct_ip = info["ip"]
            except Exception:
                summary = "（直连出口查询失败）"
                direct_ip = ""
            msg_q.put(("cancel_ok", where, summary, direct_ip))
        except Exception as e:
            msg_q.put(("cancel_fail", str(e), None, None))

    def _cancel_done(where, summary, direct_ip):
        state["working"] = False
        state["connecting"] = False
        state["info"] = None
        detail_btn.config(state="disabled")
        cancel_btn.config(state="normal")
        set_status("✓ 已恢复直连 · %s" % summary, "#1a8f3c")
        msg = ("已恢复直连（系统 + 终端代理均已清除）\n出口 IP %s" % direct_ip) if direct_ip \
              else "已恢复直连（系统 + 终端代理均已清除）"
        notify("已取消代理", msg)

    def _cancel_fail(msg):
        state["working"] = False
        state["connecting"] = False
        cancel_btn.config(state="normal")
        set_status("✗ 取消失败：%s" % msg, "#cc0000")

    def on_cancel():
        if state["working"]:
            return
        state["working"] = True
        state["connecting"] = False
        cancel_btn.config(state="disabled")
        set_status("正在取消代理…", "#0066cc")
        threading.Thread(target=_run_cancel, daemon=True).start()

    def _poll():
        try:
            while True:
                msg = msg_q.get_nowait()
                kind = msg[0]
                if kind == "connect_ok":
                    _connect_done(msg[1], msg[2], msg[3])
                elif kind == "connect_fail":
                    _connect_fail(msg[1])
                elif kind == "cancel_ok":
                    _cancel_done(msg[1], msg[2], msg[3])
                elif kind == "cancel_fail":
                    _cancel_fail(msg[1])
        except queue.Empty:
            pass
        root.after(100, _poll)

    connect_btn.config(command=on_connect)
    detail_btn.config(command=on_detail)
    cancel_btn.config(command=on_cancel)

    root.after(100, _poll)
    root.after(100, lambda: root.lift())
    root.mainloop()


def main():
    if len(sys.argv) > 1:
        cli()
    else:
        build_gui()


if __name__ == "__main__":
    main()
