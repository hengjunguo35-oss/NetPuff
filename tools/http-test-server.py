#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小 HTTP 代理测试服务端 —— 仅用于验证 NetPuff 的 http_proxy_get()。

这不是 NetPuff 的一部分，而是一个测试夹具：它按「绝对 URI」形式接收
代理请求（`GET http://host/path HTTP/1.1`），改写成源站形式后转发，
再把响应原样回传，以便在没有真实代理的情况下闭环验证
src/netpuff.py 里的 http_proxy_get()。

用法：
    python3 tools/http-test-server.py [端口]        # 默认 11081

验证：
    python3 src/netpuff.py test 127.0.0.1 11081 -p http

只监听 127.0.0.1，不对外暴露。HTTPS 代理（TLS 到代理）不在本夹具覆盖范围内。
"""
import socket
import sys
import threading
import urllib.parse


def _handle(client):
    try:
        client.settimeout(20)

        data = b""
        while b"\r\n\r\n" not in data:
            chunk = client.recv(4096)
            if not chunk:
                return
            data += chunk
        head, _, body = data.partition(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        method, uri, version = lines[0].split()

        parsed = urllib.parse.urlparse(uri.decode())
        host = parsed.hostname
        port = parsed.port or 80
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        # 绝对 URI -> 源站形式（目标服务器只认 /path）
        new_head = [b"%s %s %s" % (method, path.encode(), version)] + lines[1:]
        remote = socket.create_connection((host, port), timeout=15)
        remote.sendall(b"\r\n".join(new_head) + b"\r\n\r\n" + body)

        while True:
            chunk = remote.recv(65536)
            if not chunk:
                break
            client.sendall(chunk)
        remote.close()
    except Exception as exc:
        sys.stderr.write("http test server: %r\n" % (exc,))
    finally:
        try:
            client.close()
        except Exception:
            pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 11081
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(5)
    print("HTTP test proxy on 127.0.0.1:%d" % port, flush=True)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=_handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
