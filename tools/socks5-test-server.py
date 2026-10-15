#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小 SOCKS5 测试服务端 —— 仅用于验证 NetPuff 的 SOCKS5 客户端实现。

这不是 NetPuff 的一部分，而是一个测试夹具：它只实现 RFC 1928 的
「无认证」握手 + CONNECT（支持 IPv4 / 域名 / IPv6 三种 ATYP），
然后把双向流量对拷，以便在没有真实代理的情况下闭环验证
src/netpuff.py 里的 socks5_http_get()。

用法：
    python3 tools/socks5-test-server.py [端口]      # 默认 11080

验证：
    python3 src/netpuff.py test 127.0.0.1 11080

只监听 127.0.0.1，不对外暴露。
"""
import select
import socket
import struct
import sys
import threading


def _pipe(a, b):
    """把 a/b 两个 socket 的流量互相对拷，任一方关闭即结束。"""
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


def _handle(client):
    try:
        client.settimeout(20)

        # ① 问候：VER NMETHODS METHODS...
        head = client.recv(2)
        if len(head) < 2 or head[0] != 0x05:
            return
        client.recv(head[1])
        client.sendall(b"\x05\x00")            # 选择「无认证」

        # ② CONNECT 请求：VER CMD RSV ATYP ...
        req = client.recv(4)
        if len(req) < 4:
            return
        _, _cmd, _, atyp = req
        if atyp == 0x01:                       # IPv4
            host = socket.inet_ntoa(client.recv(4))
        elif atyp == 0x03:                     # 域名
            length = client.recv(1)[0]
            host = client.recv(length).decode()
        elif atyp == 0x04:                     # IPv6
            host = socket.inet_ntop(socket.AF_INET6, client.recv(16))
        else:
            return
        port = struct.unpack("!H", client.recv(2))[0]

        remote = socket.create_connection((host, port), timeout=15)
        # ③ 成功应答：REP=0x00 ATYP=0x01 BND.ADDR=0.0.0.0 BND.PORT=0
        client.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0")
                       + struct.pack("!H", 0))
        _pipe(client, remote)
        remote.close()
    except Exception as exc:
        sys.stderr.write("socks5 test server: %r\n" % (exc,))
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
    srv.listen(5)
    print("SOCKS5 test server on 127.0.0.1:%d" % port, flush=True)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=_handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
