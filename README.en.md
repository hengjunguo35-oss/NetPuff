# NetPuff

> A free, open-source, cross-platform system proxy switcher · **macOS / Windows**

> 🌐 中文版：**[README.md](README.md)**　·　📋 [Changelog](CHANGELOG.en.md)

<sub>ℹ️ AI-translated from the Chinese original, provided for reference only.
The Chinese version is authoritative.</sub>

> ⚠️ **For personal study, research, and communication only.** Please read the
> [Disclaimer](DISCLAIMER.en.md) and [LICENSE](LICENSE) (MIT) before use.

> ⚠️ **Windows support is not yet complete — not recommended for use.** The Windows branch
> (registry + Wininet) has not been fully verified on real hardware and may have
> compatibility issues. If you need it, feel free to fork the code and adapt it yourself.

A small tool that toggles between direct connection and a proxy with one click. Fill in
your proxy server address, click connect, and it verifies the proxy actually works and
shows you where your traffic exits; click again to restore direct connection. Also works
from the command line.

**It does not relay any traffic** — the actual egress is your own internal SOCKS5 server.
NetPuff only flips the switch and proves to you, with a real request, that it was flipped
correctly.

---

## Why

I have an internal proxy, but switching it on always meant manually editing the system
SOCKS5 settings — and the IP keeps changing when I change networks.

Worse, once set, the system settings never tell you whether it actually connected, where
the egress is, or whether you're still silently going direct.

So I wrote my own: fill in the address → verify → switch, with the egress IP shown clearly.

---

## Features

| Feature | Notes |
|---|---|
| One-click connect / disconnect | GUI buttons, or `connect` / `disconnect` on the CLI |
| Three protocols | SOCKS5 / HTTP / HTTPS (SOCKS5 by default) |
| Verify before applying | Probes the proxy with a real request before touching system config |
| Egress visibility | Shows egress IP, country/region/city, ISP, latency |
| System proxy | macOS `networksetup`; Windows registry + Wininet refresh |
| Terminal proxy | Also sets `http_proxy` etc. so curl / pip / git go through the proxy |
| Direct confirmation | After disconnect, queries your real egress IP |
| History | Remembers past IPs in a dropdown |

**What it does not do**: it provides no proxy service, relays no traffic, and ships no
nodes. You connect to *your own* proxy.

---

## Requirements

- macOS 10.13+ (the primary supported platform)
- Windows 7+ — **not yet complete, not recommended for use** (see
  [TECHNICAL.en.md · Known limitations](TECHNICAL.en.md))
- Python 3 with **tkinter** (3.10 / 3.11 / 3.12)
  - macOS: prefer the [python.org](https://www.python.org/downloads/) installer (bundles Tcl/Tk)
  - Windows: make sure to tick **"Add python.exe to PATH"** during install
- **Zero third-party dependencies** — Python standard library only

---

## Quick start

### macOS

```bash
# GUI
python3 src/netpuff.py

# Or CLI: connect + terminal proxy
python3 src/netpuff.py connect 192.168.1.100 2080 -t

# Restore direct
python3 src/netpuff.py disconnect
```

Build a double-clickable `.app`:

```bash
./app/build-app.sh          # produces NetPuff.app
```

### Windows

> ⚠️ **Not yet complete — not recommended for use.** The following is for reference only;
> it has not been fully verified on real hardware. Feel free to fork and adapt the code.

```
double-click  app\启动NetPuff.bat
```

> Requires `python` or `pythonw` on PATH (tick "Add python.exe to PATH" when installing).

---

## CLI usage

```
python3 src/netpuff.py status                  # show system proxy state
python3 src/netpuff.py test  <IP> [port]       # test proxy only, don't change system
python3 src/netpuff.py connect <IP> [port] [-t] # test + enable; -t also sets terminal proxy
python3 src/netpuff.py disconnect              # restore direct
python3 src/netpuff.py direct                  # show direct egress IP
```

`-p socks5|http|https` selects the protocol (default socks5).

---

## How it works (briefly)

1. **Probe** — send a real request through the proxy (via raw socket) to ip-api.com,
   get egress IP / geolocation / latency. This happens *before* touching system config.
2. **System proxy** — `networksetup` on macOS; registry + Wininet refresh on Windows.
3. **Terminal proxy** — write `http_proxy` etc. to shell rc or user env vars, with a
   `no_proxy` allowlist for internal networks.
4. **Disconnect** — clear both in reverse.

The hard part is implementing SOCKS5 by hand — the stdlib's urllib has no socks support,
so the RFC 1928 handshake is done over raw sockets. See [TECHNICAL.en.md](TECHNICAL.en.md).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| "port not open" | The proxy server is down, or the IP changed. Try `test <IP>` first |
| Fails after changing networks | The internal proxy IP changes with the network — update it |
| curl still goes direct | Terminal proxy only affects *new* shells; `source ~/.zshrc` or reopen |
| Some Windows apps ignore the proxy | Windows system SOCKS relies on IE settings (see technical doc) |
| Internal network slow/broken | Check that `no_proxy` covers your internal subnets |

---

## Project layout

```
src/netpuff.py        All logic (single file, per-function comments)
app/启动NetPuff.command    macOS double-click launcher
app/启动NetPuff.bat        Windows double-click launcher
app/build-app.sh             Package into NetPuff.app
```

## Privacy

**Local tool — collects and uploads nothing.** The only network call is the one-time
egress geolocation query to ip-api.com (to show "where you're exiting from"). History
lives only in your local `~/.netpuff_history.json`.

## License

**MIT** — see [LICENSE](LICENSE). Free to use, modify, and distribute with attribution.
