# Changelog

<sub>ℹ️ AI-translated from the Chinese original ([CHANGELOG.md](CHANGELOG.md)), provided for
reference only. The Chinese version is authoritative.</sub>

This project follows [Semantic Versioning](https://semver.org/).

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
