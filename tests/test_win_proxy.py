# -*- coding: utf-8 -*-
"""Windows 快照/还原的不变式测试。

用真实 winreg API，但写在影子键
    HKCU\\Software\\NetPuff\\Test\\<uuid>\\...
里，不碰用户真实的 Internet Settings / Environment。
"""
import os
import sys
import tempfile
import unittest
import uuid
import winreg

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC)
import netpuff as np  # noqa: E402


def _deltree(path):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return
    try:
        count = winreg.QueryInfoKey(key)[0]
        names = [winreg.EnumKey(key, i) for i in range(count)]
    finally:
        winreg.CloseKey(key)
    for name in names:
        _deltree(path + "\\" + name)
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)


class WinProxyStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = r"Software\NetPuff\Test\%s" % uuid.uuid4().hex
        cls.inet = cls.root + r"\Internet Settings"
        cls.envk = cls.root + r"\Environment"
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls.inet)
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls.envk)

    @classmethod
    def tearDownClass(cls):
        _deltree(cls.root)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._old = (np.WIN_INET_KEY_PATH, np.WIN_ENV_KEY_PATH,
                     np.WIN_STATE_FILE, np._win_refresh)
        np.WIN_INET_KEY_PATH = self.inet
        np.WIN_ENV_KEY_PATH = self.envk
        np.WIN_STATE_FILE = os.path.join(self.tmp, "state.json")
        np._win_refresh = lambda: None
        self._clear(self.inet)
        self._clear(self.envk)
        if os.path.exists(np.WIN_STATE_FILE):
            os.remove(np.WIN_STATE_FILE)

    def tearDown(self):
        (np.WIN_INET_KEY_PATH, np.WIN_ENV_KEY_PATH,
         np.WIN_STATE_FILE, np._win_refresh) = self._old

    # ---- helpers -------------------------------------------------
    def _clear(self, path):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                             winreg.KEY_READ | winreg.KEY_SET_VALUE)
        try:
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, 0)
                except OSError:
                    break
                winreg.DeleteValue(key, name)
        finally:
            winreg.CloseKey(key)

    def _set(self, path, name, value):
        typ = winreg.REG_DWORD if isinstance(value, int) else winreg.REG_SZ
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.SetValueEx(key, name, 0, typ, value)
        finally:
            winreg.CloseKey(key)

    def _get(self, path, name):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ)
            try:
                return winreg.QueryValueEx(key, name)[0]
            finally:
                winreg.CloseKey(key)
        except FileNotFoundError:
            return None

    # ---- cases ---------------------------------------------------
    def test_apply_then_restore_is_exact(self):
        self._set(self.inet, "ProxyEnable", 0)
        self._set(self.inet, "ProxyServer", "127.0.0.1:7897")

        np.win_apply_proxy("1.2.3.4", "8080", "socks5")
        self.assertEqual(self._get(self.inet, "ProxyEnable"), 1)
        self.assertEqual(self._get(self.inet, "ProxyServer"), "socks=1.2.3.4:8080")
        self.assertIn("<local>", self._get(self.inet, "ProxyOverride") or "")

        np.win_restore_proxy()
        self.assertEqual(self._get(self.inet, "ProxyEnable"), 0)
        self.assertEqual(self._get(self.inet, "ProxyServer"), "127.0.0.1:7897")
        self.assertIsNone(self._get(self.inet, "ProxyOverride"))
        self.assertFalse(os.path.exists(np.WIN_STATE_FILE))

    def test_double_connect_keeps_original(self):
        self._set(self.inet, "ProxyEnable", 1)
        self._set(self.inet, "ProxyServer", "corp.internal:3128")

        np.win_apply_proxy("1.1.1.1", "1080", "socks5")
        np.win_apply_proxy("2.2.2.2", "2080", "socks5")
        np.win_restore_proxy()

        self.assertEqual(self._get(self.inet, "ProxyServer"), "corp.internal:3128")
        self.assertEqual(self._get(self.inet, "ProxyEnable"), 1)

    def test_http_scheme_maps_both_protocols(self):
        np.win_apply_proxy("1.2.3.4", "8080", "http")
        self.assertEqual(self._get(self.inet, "ProxyServer"),
                         "http=1.2.3.4:8080;https=1.2.3.4:8080")
        np.win_restore_proxy()

    def test_override_keeps_user_entries(self):
        self._set(self.inet, "ProxyOverride", "*.corp.example")
        np.win_apply_proxy("1.2.3.4", "8080", "socks5")
        value = self._get(self.inet, "ProxyOverride")
        self.assertIn("*.corp.example", value)
        self.assertIn("<local>", value)
        np.win_restore_proxy()
        self.assertEqual(self._get(self.inet, "ProxyOverride"), "*.corp.example")

    def test_env_restore_brings_back_user_value(self):
        self._set(self.envk, "http_proxy", "http://corp-proxy:3128")
        self._set(self.inet, "ProxyEnable", 0)

        np.win_apply_proxy("1.2.3.4", "8080", "socks5")
        np.win_set_terminal_proxy("1.2.3.4", "8080", "socks5")
        self.assertEqual(self._get(self.envk, "http_proxy"), "socks5h://1.2.3.4:8080")
        self.assertEqual(self._get(self.envk, "no_proxy"), np.NO_PROXY)

        np.win_restore_proxy()
        np.win_clear_terminal_proxy()
        self.assertEqual(self._get(self.envk, "http_proxy"), "http://corp-proxy:3128")
        self.assertIsNone(self._get(self.envk, "all_proxy"))

    def test_env_never_touches_foreign_vars_without_state(self):
        self._set(self.envk, "https_proxy", "http://user:8080")
        msg = np.win_clear_terminal_proxy()
        self.assertIn("未发现", msg)
        self.assertEqual(self._get(self.envk, "https_proxy"), "http://user:8080")

    def test_no_state_only_closes_switch(self):
        self._set(self.inet, "ProxyEnable", 1)
        self._set(self.inet, "ProxyServer", "someone.else:8080")
        np.win_restore_proxy()
        self.assertEqual(self._get(self.inet, "ProxyEnable"), 0)
        self.assertEqual(self._get(self.inet, "ProxyServer"), "someone.else:8080")


if __name__ == "__main__":
    unittest.main(verbosity=2)
