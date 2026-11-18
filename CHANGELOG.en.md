# Changelog

<sub>ℹ️ AI-translated from the Chinese original ([CHANGELOG.md](CHANGELOG.md)), provided for
reference only. The Chinese version is authoritative.</sub>

This project follows [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2026-11-18

Windows hardening: snapshot before writing, exact restore on disconnect, plus a SOCKS4 preflight.

- **Windows compatibility mode (on by default)**: WinINet speaks SOCKS4 only and resolves
  host names locally, so poisoned DNS yields wrong IPs. When connecting through SOCKS5,
  NetPuff now starts a local HTTP→SOCKS5 bridge on `127.0.0.1` and points the system proxy
  at `http=127.0.0.1:port`; HTTPS uses CONNECT, so the upstream resolves the host name.
  Verified to open x.com / google.com through the system proxy. The bridge is stopped on
  disconnect; set `NETPUFF_NO_BRIDGE=1` to fall back to plain SOCKS4 mode.
- **System proxy snapshot / restore**: before writing, `ProxyEnable / ProxyServer /
  ProxyOverride / AutoConfigURL` and eight proxy environment variables are captured to
  `~/.netpuff_win_state.json`. Disconnect restores only values that are still ours;
  anything you changed meanwhile is left alone with a notice. Without a snapshot it only
  turns the switch off and **never guesses your original address**.
- **SOCKS4 preflight**: Windows' system layer (WinINet) only speaks SOCKS4; a PAC that
  returns SOCKS5 is silently ignored and falls back to DIRECT. NetPuff now probes SOCKS4
  before writing the registry and fails with a clear message if it is unsupported
  (`-t` still gives you terminal-only proxying).
- **ProxyOverride**: `<local>` plus private ranges (`10.*`, `172.16.*`–`172.31.*`,
  `192.168.*`; this field supports wildcards only, not CIDR), merged with your existing
  entries and restored on disconnect.
- **Terminal variables**: written through `HKCU\Environment` + `WM_SETTINGCHANGE` instead
  of `setx` (no `SUCCESS:` noise, no 1024-character truncation); eight variables including
  upper/lower case and `no_proxy`; cleanup deletes only values NetPuff wrote and restores
  any value you had before.
- **`-t` semantics**: `connect` without `-t` no longer clears the terminal proxy.
- **CLI**: invalid ports and protocol failures no longer raise uncaught tracebacks;
  argument errors exit 2, runtime failures exit 3; `status` no longer prints a server
  address while disabled.
- **Probing**: responses are read by `Content-Length`, so a keep-alive server no longer
  causes a 15-second timeout.
- **IPv6**: `[IPv6]:port` is supported in the registry, history and environment variables.
- **GUI**: DPI awareness, Windows fonts/theme, platform-specific success text, disabled
  cancel button at startup, and the quit dialog now receives its parent window.
- **Tests**: added `tools/socks45-test-server.py` (SOCKS4/4a/5 test server) and `tests/`
  (12 cases; registry tests use shadow keys and never touch your real settings).
- **Packaging**: Windows single-file exe and Inno Setup installer (per-user, no admin
  rights, no Python required); the macOS `.app` and window now share the new icon;
  a new `windows-build.yml` builds and attaches artifacts on `v*` tags.

---

## [1.1.0] — 2026-10-30

Added quit protection and startup auto-detection, so the proxy never stays enabled
without you knowing.

- **Quit protection**: closing the window while the system proxy is still on now raises a
  **native system dialog** offering "restore and quit" / "quit only" / "cancel". Restoring
  clears both the system proxy and the terminal proxy before exiting; if the proxy is
  already off, you are not bothered. On macOS, Cmd+Q is intercepted too — otherwise the
  shortcut would bypass the confirmation.
- **Startup auto-detection**: on launch the app scans the system proxy configuration. If a
  proxy is still active it immediately switches the status bar to "⚠ proxying", fills in
  the detected address, and probes the egress asynchronously; the
  "cancel proxy / restore direct" button disables it in one click. This covers the
  "I chose quit-only last time and now want to turn the proxy off" case.
- The close decision is based on the **actual system state**, not a cached in-memory flag,
  so toggling the proxy outside the app is detected correctly.
- Status-bar text is now truncated with an ellipsis instead of being silently clipped.
- `get_proxy_detail()`: new helper that reads the system proxy protocol/address/port for
  startup detection and egress probing (on Windows it parses multi-protocol `ProxyServer`
  maps, preferring socks > http > https).
- Fixed: the macOS dialog script wrongly used `with icon caution` (a `display dialog`
  parameter), which made `display alert` fail to compile; now uses `as warning`.

---

## [1.0.2] — 2026-10-15

Fixed a Windows output-encoding crash and split CI into its own workflow.

- **Fixed**: on Windows, console or redirected output encoding is usually not UTF-8
  (e.g. CP1252 / CP936), so printing Chinese raised `UnicodeEncodeError` and crashed the
  CLI (for example `python netpuff.py status > out.txt`). stdout/stderr are now switched
  to UTF-8 at startup, with unencodable characters replaced.
- Added `ci.yml`: runs smoke checks on **both macOS and Windows** for pushes to main and
  pull requests (syntax, version consistency, CLI, protocol end-to-end, `.bat` line
  endings). Windows steps use bash throughout, avoiding false "every step failed" results
  caused by PowerShell quoting and encoding differences.
- Slimmed `release.yml` down to building and publishing on tags; the Windows checks moved
  into `ci.yml`.

---

## [1.0.1] — 2026-10-15

Packaging and documentation improvements (**no functional changes**).

- Added a macOS **`.dmg`** alongside the existing `.zip`, matching the usual macOS install
  experience: it contains `NetPuff.app` plus a shortcut to `/Applications`
- Added a **Windows package**: **not yet complete, not recommended for daily use**. It is
  provided so that contributors can unzip, run, patch, and submit changes
  (see `README-Windows.txt` inside the package)
- Release notes now cover both macOS and Windows, in Chinese and English, and explicitly
  mark Windows as incomplete
- README gained a "Verification" section documenting reproducible checks and their results
- Added a **non-blocking** Windows smoke test (syntax, CLI, registry read path, `.bat` line
  endings)

---

## [1.0.0] — 2026-10-14

First stable release.

- Cross-platform system proxy switching (macOS / Windows), with both a GUI and a CLI
- Three proxy protocols supported: SOCKS5 / HTTP / HTTPS
- macOS: system proxy via `networksetup`, with automatic detection of the active network
  service (Wi-Fi / wired)
- Windows: registry `Internet Settings` + Wininet refresh
- Terminal proxy: writes `http_proxy / https_proxy / all_proxy` into the shell rc (macOS) or
  user environment variables (Windows), together with an internal-network `no_proxy` allowlist
- Probes the proxy for availability *before* writing system configuration, so a dead address
  is never applied
- Queries egress IP / geolocation / latency through the proxy; also reports your real egress
  when connected directly
- Remembers previously used proxy addresses (`~/.netpuff_history.json`)
- SOCKS5 implemented by hand (RFC 1928, no-auth + domain forwarding); zero third-party
  dependencies
- License: MIT
