# SteamAutoCracker v2.3.0-wft.1

> **Hotfix rebuild (2026-10-01):** fixes the compiled EXE exiting at startup with `AttributeError: module 'ttkbootstrap' has no attribute 'BOTH'`. The release builder now injects the missing classic Tk constants before the GUI starts, covering `BOTH`, `LEFT`, `RIGHT`, `Y`, `END`, `NORMAL`, and `DISABLED`.

First maintained release of the wefalltomorrow best-of fork, based on upstream 2.2.2.

## Highlights

- Fixes the all-games `KeyError` failure reported in upstream issue #124.
- Replaces the obsolete local Steam app list with live Steam Store title search.
- Adds Light, Dark and Black themes.
- Adds a resizable GUI and expandable/scrollable logs.
- Replaces `pywin32` version detection with portable `pefile` parsing.
- Improves HTTP retry handling and PyInstaller/resource paths.
- Prevents the upstream autoupdater from silently overwriting this fork.
- Adds Python 3.10/3.13 CI plus an issue #124 regression test.
- Adds a reproducible one-file Windows PyInstaller build.

## Issue #124

Steam can return valid JSON from AppDetails without the requested dynamic AppID key. Upstream indexed that key directly and crashed with `KeyError`.

This release validates the response, retries once without `filters=basic`, handles incomplete responses cleanly, and applies the same defensive path to DLC-name lookups.

## Included community work

Useful fixes and ideas were selectively integrated from the Sir-Kam, codingforfun5435 and sign-river forks and from upstream pull requests. Divergent or experimental changes were reviewed but not blindly merged.

See `CHANGELOG.md` for the full release breakdown.

## Downloads

- `Steam.Auto.Cracker.GUI.v2.3.0-wft.1.zip` — compiled 64-bit Windows release.
- `Steam.Auto.Cracker.GUI.v2.3.0-wft.1.zip.sha256` — SHA-256 checksum.

The release executable is built by GitHub Actions from the tagged repository source.
