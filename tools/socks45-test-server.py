#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小 SOCKS4 / SOCKS4a / SOCKS5 测试服务端（仅本地闭环验证）。

为什么需要它：Windows 系统代理只会说 SOCKS4，而 NetPuff 的探针说的是
SOCKS5。要在一台机器上同时验证这两条路径，测试服务端必须两种协议都收。

只监听 127.0.0.1，不对外暴露。

用法：
    python tools/socks45-test-server.py [端口]
"""
import select
import socket
import struct
import sys
import threading


def pipe(a, b):
    try:
        while True:
            readable, _, _ = select.select([a, b], [], [], 30)
            if not readable:
                return
            for s in readable:
                data = s.recv(65536)
                if not data:
                    return
                (b if s is a else a).sendall(data)
    except Exception:
        pass


def handle(client):
    try:
        client.settimeout(20)
        ver = client.recv(1)
        if not ver:
            return
        if ver[0] == 0x05:
            n = client.recv(1)[0]
            client.recv(n)
            client.sendall(b"\x05\x00")
            head = client.recv(4)
            _, cmd, _, atyp = head
            if cmd != 0x01:
                return
            if atyp == 0x01:
                host = socket.inet_ntoa(client.recv(4))
            elif atyp == 0x03:
                ln = client.recv(1)[0]
                host = client.recv(ln).decode("utf-8", "replace")
            elif atyp == 0x04:
                host = socket.inet_ntop(socket.AF_INET6, client.recv(16))
            else:
                return
            port = struct.unpack("!H", client.recv(2))[0]
            remote = socket.create_connection((host, port), timeout=15)
            client.sendall(b"\x05\x00\x00\x01" + b"\x00" * 6)
            print("SOCKS5 -> %s:%s" % (host, port), flush=True)
            threading.Thread(target=pipe, args=(client, remote), daemon=True).start()
            pipe(remote, client)
            remote.close()
            return

        if ver[0] == 0x04:
            rest = client.recv(7)
            if len(rest) < 7:
                return
            cmd = rest[0]
            port = struct.unpack("!H", rest[1:3])[0]
            ip = rest[3:7]
            while True:                       # userid
                b = client.recv(1)
                if not b or b == b"\x00":
                    break
            if ip[:3] == b"\x00\x00\x00" and ip[3] != 0:   # SOCKS4a
                domain = b""
                while True:
                    b = client.recv(1)
                    if not b or b == b"\x00":
                        break
                    domain += b
                host = domain.decode("utf-8", "replace")
                kind = "SOCKS4a"
            else:
                host = socket.inet_ntoa(ip)
                kind = "SOCKS4"
            remote = socket.create_connection((host, port), timeout=15)
            client.sendall(b"\x00\x5a" + struct.pack("!H", 0) + b"\x00\x00\x00\x00")
            print("%s -> %s:%s" % (kind, host, port), flush=True)
            threading.Thread(target=pipe, args=(client, remote), daemon=True).start()
            pipe(remote, client)
            remote.close()
            return

        print("unknown version 0x%02x" % ver[0], flush=True)
    except Exception as exc:
        print("handler error: %r" % (exc,), flush=True)
    finally:
        try:
            client.close()
        except Exception:
            pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 11080
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(8)
    print("SOCKS4/4a/5 test server on 127.0.0.1:%d" % port, flush=True)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
