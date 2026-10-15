# Changelog

<sub>ℹ️ AI-translated from the Chinese original ([CHANGELOG.md](CHANGELOG.md)), provided for
reference only. The Chinese version is authoritative.</sub>

This project follows [Semantic Versioning](https://semver.org/).

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
