# -*- coding: utf-8 -*-
"""与平台无关的小工具测试：IPv6 地址格式、HTTP 正文读取。"""
import os
import socket
import sys
import threading
import unittest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC)
import netpuff as np  # noqa: E402


class HostPortTests(unittest.TestCase):
    def test_ipv4(self):
        self.assertEqual(np.hostport("10.1.2.3", 2080), "10.1.2.3:2080")

    def test_ipv6_gets_brackets(self):
        addr = "2408:8421:b30:eb0:30be:c5ff:fe38:b978"
        self.assertEqual(np.hostport(addr, 2080), "[%s]:2080" % addr)

    def test_brackets_normalized(self):
        self.assertEqual(np.normalize_host("[::1]"), "::1")
        self.assertEqual(np.hostport("[::1]", 1080), "[::1]:1080")

    def test_proxy_server_value_ipv6(self):
        self.assertEqual(np._proxy_server_value("[::1]", 1080, "socks5"),
                         "socks=[::1]:1080")


class ReadBodyTests(unittest.TestCase):
    def test_content_length_stops_without_eof(self):
        a, b = socket.socketpair()
        a.settimeout(5)

        def server():
            b.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello")
            # 故意不关闭连接，模拟「服务端保持 keep-alive」
            threading.Event().wait(3)
            b.close()

        threading.Thread(target=server, daemon=True).start()
        try:
            self.assertEqual(np._read_http_body(a), b"hello")
        finally:
            a.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
