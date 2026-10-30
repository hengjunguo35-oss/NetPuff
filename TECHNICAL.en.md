# NetPuff Technical Documentation

> Version: `NetPuff` v1.0.0 · Platforms: macOS / Windows · Author: hengjunguo35-oss
>
> 🌐 中文版：**[技术文档.md](技术文档.md)**

<sub>ℹ️ AI-translated from the Chinese original, provided for reference only.
The Chinese version is authoritative.</sub>

---

## 1. What problem this solves

**Input**: a proxy server address (IP + port + protocol).

**Output**: system proxy and terminal proxy both set, plus a clear readout of the egress
IP / country / ISP / latency proving it actually worked.

**What it deliberately does not do** (hard constraints, not "not yet implemented"):

| Does not | Why |
|---|---|
| Relay traffic | The egress is your own server; NetPuff is only a switch + probe |
| Ship any nodes | Provides, bundles, and recommends no proxy service |
| Collect data | The only network call is the egress geolocation query |

**Core requirement: "connected or not, and from where" must be verifiable at a glance.**

---

## 2. How it works

### 2.1 Core idea: verify first, then switch

The fatal flaw of most system-proxy tools is that they **write the address first and only
then discover it's dead** — leaving the user offline with no idea what went wrong.

NetPuff reverses the order:

```
fill address ──▶ probe (query egress through proxy) ──✗ fail──▶ report error, don't touch system
                       │
                       └─✔ ok──▶ apply system proxy + terminal proxy
```

The probe uses a raw socket to talk to the proxy directly (**not** through the system
proxy, which isn't set yet), so it tests the proxy itself, not an already-polluted path.

### 2.2 Hand-written SOCKS5: why implement the protocol at all

Python's stdlib `urllib` only honors `http_proxy` / `https_proxy` — it has no socks
support. The common fix is pulling in `requests[socks]` or `PySocks`, which breaks the
"zero third-party dependencies" goal.

So `socks5_http_get()` implements the RFC 1928 no-auth handshake over a raw socket:

```
① greeting     client → server : 05 01 00           (SOCKS5, 1 method, no-auth)
               server → client : 05 00              (no-auth accepted)

② CONNECT      client → server : 05 01 00 03 <len> <hostname> <port>
                                                    (CMD=CONNECT, ATYP=domain)
               server → client : 05 00 00 <ATYP> <bind addr> <bind port>

③ data         tunnel is up; send the real HTTP/HTTPS
```

A key design choice: **send the hostname (not the resolved IP) to the proxy** (`ATYP=0x03`),
letting the proxy resolve the domain on its side. This matches curl's `socks5h://` semantics
— the domain resolves at the egress, which sidesteps local DNS pollution. That's also why
the terminal proxy writes `socks5h://` rather than `socks5://`.

The reply's "bind address" has a variable length (IPv4 = 4 bytes / domain = variable /
IPv6 = 16 bytes); the code branches on `ATYP` and skips exactly the right number of bytes,
avoiding protocol desynchronization.

### 2.3 System proxy: two platforms, two paths

The system proxy governs GUI programs (browsers), and the mechanism differs entirely
between macOS and Windows.

**macOS — `networksetup`**

```
networksetup -setsocksfirewallproxy  <service> <host> <port>   # write address
networksetup -setsocksfirewallproxystate <service> on           # turn it on
```

Two things worth noting:

1. Address and switch are **two separate commands** — both must run.
2. The command wants a "network service name" (`Wi-Fi` / `Ethernet`), not an interface
   name (`en0`). A machine can have Wi-Fi, Thunderbolt, and USB adapters simultaneously;
   hardcoding `Wi-Fi` would configure the wrong one. So `mac_primary_service()` first finds
   the default route's interface, then maps it back to the service name.

**Windows — registry + Wininet refresh**

```
HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings
    ProxyEnable  = 1
    ProxyServer  = "socks=192.168.1.100:2080"
```

Changing the registry alone isn't enough — running programs won't re-read it. You must
broadcast two events via Wininet:

| Value | Constant | Purpose |
|---|---|---|
| 39 | `INTERNET_OPTION_SETTINGS_CHANGED` | re-read proxy settings |
| 37 | `INTERNET_OPTION_REFRESH` | reconnect existing connections |

These are well-known magic numbers (MSDN offers no named constants), so the code uses the
raw values with comments.

### 2.4 Terminal proxy: the other path for CLI tools

The system proxy only governs GUI programs; `curl` / `pip` / `git` only honor environment
variables. So both must be set for terminal tools to actually go through the proxy.

On macOS, a marked block is appended to `~/.zshrc`:

```bash
# >>> NetPuff 终端代理 >>>
export http_proxy="socks5h://192.168.1.100:2080"
export https_proxy="socks5h://192.168.1.100:2080"
export all_proxy="socks5h://192.168.1.100:2080"
export no_proxy="localhost,127.0.0.1,::1,10.0.0.0/8,192.168.0.0/16,172.16.0.0/12"
# <<< NetPuff 终端代理 <<<
```

Subtle details:

- **Both cases are set**: curl reads lowercase, some legacy programs only uppercase — set both.
- **`no_proxy` allowlist**: without it, requests to internal `10.x` / `192.168.x` services
  get routed into the proxy — a common and very sneaky trap.
- **Marked-block deletion**: on disconnect, only the block between the markers is removed,
  **never touching the user's other .zshrc config**.

On Windows, `setx` writes user environment variables (equivalent effect; no rc-file concept).

### 2.5 GUI: bridging a single-threaded UI and background networking

Tk's UI is single-threaded — doing a socket connect/wait on the main thread would freeze the
window. So all network work is pushed to a `daemon` thread, results are returned through a
`queue.Queue`, and `root.after` polls the queue back onto the UI thread:

```
click "connect" ──▶ on_connect() ──▶ worker thread _run_connect()  (network I/O)
                                        │  put into msg_q
UI thread _poll() every 100ms ──▶ read msg_q ──▶ update label / notify
```

The "connecting…" animation is also driven by recursive `root.after` scheduling
(`_animate_connect`) — non-blocking, no extra thread.

### 2.6 Quit protection and startup self-check: never leave the proxy behind

The proxy is **system-level** state, while the app is just a switch — quitting the app does
not disable the proxy. That is the easiest trap to fall into: you assume quitting cleaned
up, while the system proxy still points at that server. Two mechanisms close the gap.

**Ask before closing**

`root.protocol("WM_DELETE_WINDOW", on_close)` takes over window close. On macOS, Cmd+Q does
not go through that event, so `root.createcommand("::tk::mac::Quit", on_close)` hooks it as
well. `on_close` decides as follows:

1. Call `get_proxy_detail()` to read the **real system state** — never the cached in-memory
   flag, because the user may well have toggled the proxy in System Settings;
2. Not enabled → quit silently;
3. Still enabled → raise a **native** dialog (macOS `osascript display alert`, Windows
   `MessageBoxW`) with three options:
   - **Restore and quit** → run `clear_system_proxy()` + `clear_terminal_proxy()`, then quit
   - **Quit only** → keep the proxy, quit
   - **Cancel** → stay in the app

> Two macOS gotchas:
> ① `display alert` takes `as warning` for the icon; `with icon caution` belongs to
> `display dialog` and makes the script **fail to compile** (this project hit exactly that
> in v1.1.0);
> ② clicking the `cancel button` and pressing Esc both return a non-zero exit code, so
> "Cancel" must be its own button rather than borrowing one of the other two options.

**Detect on launch**

400 ms after startup (so the window is drawn) a worker thread runs `get_proxy_detail()` and
sends the result back through the queue. If a system proxy is still enabled:

- the status bar immediately becomes "⚠ system proxy still enabled · host:port", and the
  detected address / port / protocol are **filled into the form**;
- `fetch_exit_info()` then probes the egress asynchronously: on success the status is
  upgraded to "⚠ proxying · egress IP · country city", otherwise it degrades to
  "system proxy still on · probe failed" — either way a one-click disconnect is available;
- the disconnect entry point is the existing "cancel proxy / restore direct" button —
  **no new widgets**.

This is exactly the complement to "quit only" chosen above: when you later want the proxy
off, reopen the app, see the current state, and restore with one click instead of digging
through System Settings.

---

## 3. Technology choices

### 3.1 Language & toolchain

| Tech | Role |
|---|---|
| **Python 3** | All logic (GUI + CLI + network + platform adaptation) |
| **tkinter** | GUI (stdlib) |
| **socket / ssl** | raw-socket SOCKS5 / HTTP proxy probing |
| **subprocess** | calls `networksetup` / `route` / `setx` |
| **winreg / ctypes** | Windows registry & Wininet refresh |
| **zsh / cmd scripts** | macOS `.command` and Windows `.bat` launchers |

### 3.2 The zero-dependency trade-offs

| Need | Stdlib approach |
|---|---|
| SOCKS5 probing | hand-written RFC 1928 handshake over raw socket |
| HTTPS probing | wrap the socket with `ssl.create_default_context()` |
| System proxy | `subprocess` system commands / `winreg` |
| Notification | macOS `osascript` to Notification Center |

> The cost: ~40 lines of hand-written SOCKS5 instead of a one-line `requests.get(proxies=…)`.
> The payoff: double-click to run, no `pip install` of anything.

### 3.3 Why Python

- **Cross-platform**: one codebase for macOS and Windows (branched on `sys.platform`).
- **tkinter is stdlib**: GUI with no extra deps — the user just installs official Python.
- **Readable & editable**: plain `.py`, ideal for a tool of this size.

The cost: distribution requires Python (no single compiled binary like Swift/Go), though on
macOS the `.app` shell wraps the Python call so the experience is identical.

---

## 4. Environment setup

### 4.1 Requirements

| Item | Requirement |
|---|---|
| macOS | 10.13+ (`networksetup` has existed for ages; older untested) |
| Windows | 7+ |
| Python | 3.10 / 3.11 / 3.12, with tkinter |
| Dependencies | none |

When installing Python, **make sure tcl/tk is included**:
- macOS official installer bundles Tcl/Tk; Homebrew `python@3.12` may lack `_tkinter`
- Windows installer bundles tcl/tk by default

### 4.2 Package a double-clickable .app (macOS)

```bash
./app/build-app.sh              # output into the project root (CI uses this)
./app/build-app.sh dist         # or into dist/ to keep the root tidy
```

The output is a self-contained `NetPuff.app` — a zsh launcher plus the embedded
`netpuff.py`. Double-clicking auto-discovers a tkinter-capable Python and launches
the GUI; the target machine needs neither the source nor any packages.

### 4.3 Gatekeeper on first run

If the `.app` arrives via cloud drive/download, it carries a quarantine flag:

```bash
# Option 1: right-click the app → Open (once)
# Option 2:
xattr -dr com.apple.quarantine /path/to/NetPuff.app
```

---

## 5. Usage

### 5.1 CLI

```bash
python3 src/netpuff.py status
python3 src/netpuff.py test    192.168.1.100 2080
python3 src/netpuff.py connect 192.168.1.100 2080 -t
python3 src/netpuff.py disconnect
python3 src/netpuff.py direct
```

### 5.2 GUI

Fill IP / port → pick protocol → (optional) tick "also set terminal proxy" → Connect →
"Details" for full info; "Disconnect" to restore direct.

---

## 6. Known limitations

1. **Windows support is not yet complete — not recommended for use**: the Windows branch is
   implemented (registry `Internet Settings` + Wininet refresh + `setx` env vars) but has
   **not been fully verified on real hardware** and may have compatibility issues. It is
   **not recommended for use on Windows** at this time. If you need it, feel free to fork
   and adapt the code — the relevant parts are the `IS_WIN` branches of
   `set_system_proxy()` / `clear_system_proxy()` and `set_terminal_proxy()` /
   `clear_terminal_proxy()`.
2. **Windows system SOCKS relies on IE settings**: only programs that follow the system
   proxy are affected (Chrome/Edge do; Firefox doesn't by default; some native apps don't).
   This is an inherent Windows-platform limitation, not a bug.
3. **Terminal proxy only affects *new* shells**: already-open terminals won't re-read rc.
4. **Internal proxy IP changes**: the proxy address may change when you change networks.
5. **HTTP/HTTPS proxy support is basic**: designed primarily for SOCKS5; HTTP uses absolute
   URI form and doesn't cover authenticated proxies (the target use case is a no-auth
   internal proxy).
6. **The probe is plain HTTP**: the egress query goes to `http://ip-api.com` (free, rate-
   limited), not HTTPS — but it carries nothing sensitive beyond your egress info.

---

## 7. Project layout

```
NetPuff/
├── README.md / README.en.md              overview (zh / en)
├── 技术文档.md / TECHNICAL.en.md          this document (zh / en)
├── 免责声明.md / DISCLAIMER.en.md         disclaimer & terms (zh / en)
├── LICENSE                               MIT
├── CHANGELOG.md / CHANGELOG.en.md        changelog (zh / en)
├── .github/
│   ├── workflows/release.yml             build & publish releases on v* tags
│   └── release-notes.md                  release notes (zh / en)
├── src/
│   └── netpuff.py                 all logic (single file, per-function comments)
├── app/
│   ├── 启动NetPuff.command            macOS double-click launcher
│   ├── 启动NetPuff.bat                Windows double-click launcher
│   ├── build-app.sh                      package into NetPuff.app
│   └── README-Windows.txt            notes shipped inside the Windows package
└── tools/
    ├── socks5-test-server.py        minimal SOCKS5 test server (verification)
    └── http-test-server.py          minimal HTTP proxy test server (verification)
```

### Suggested reading order

1. The **file header comment** at the top of `src/netpuff.py` — build the big picture
2. `socks5_http_get()` — the hand-written SOCKS5 handshake, the core
3. `set_system_proxy()` / `clear_system_proxy()` — the two platforms' system-proxy branches
4. `set_terminal_proxy()` — terminal env vars and marked-block deletion
5. `_run_connect` / `_poll` in `build_gui()` — the GUI thread + queue pattern
6. `on_close()` and `get_proxy_detail()` — quit protection and startup self-check

---

## License

**MIT**, see [LICENSE](LICENSE).
