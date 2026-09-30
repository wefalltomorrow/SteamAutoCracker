# Changelog

All notable changes to the wefalltomorrow SteamAutoCracker fork are documented here.

## 2.3.0-wft.1 — 2026-10-01

### Hotfix rebuild

- Fixed the compiled EXE failing before the GUI opens because `ttkbootstrap` was used as the `tk` alias but does not export classic Tk constants such as `BOTH`.
- Added a PyInstaller runtime compatibility hook for all affected constants and CI coverage for the startup path.

First maintained best-of fork release, based on upstream SteamAutoCracker 2.2.2.

### Added

- Light, Dark and Black GUI themes.
- Resizable main window with an expandable, scrollable monospaced log view.
- Live Steam Store title search instead of the obsolete local/GetAppList flow.
- Windows CI coverage on Python 3.10 and 3.13.
- Dedicated regression coverage for the missing-AppID response reported in upstream issue #124.
- Reproducible PyInstaller Windows release workflow and SHA-256 release checksums.
- Portable PE version parsing through `pefile`.

### Fixed

- Steam AppDetails no longer crashes with `KeyError` when Steam returns valid JSON without the requested AppID key.
- AppDetails retries once without `filters=basic` when the first response is empty or missing the requested key.
- `RetrieveGame()` and DLC-name retrieval now validate incomplete/unexpected Steam responses before using them.
- HTTP requests use bounded iterative retries rather than recursive retry calls.
- Folder selection handles tuple-style Tk return values.
- Config/log/resource paths work correctly from source and PyInstaller builds.
- Steamless is resolved from the bundled resource path.
- Theme reset immediately refreshes the UI.
- Startup error logging works even when an import fails before application helpers are initialized.

### Changed

- Replaced the `pywin32` / `win32api` version dependency with `pefile`.
- Upstream update checks no longer replace this fork with BigBoiCJ's executable; newer upstream releases open in the browser instead.
- README/download badges and release links now point to the maintained fork.
- Added explicit Steam request headers plus English/US Store API parameters for more predictable metadata responses.

### Community sources reviewed

The fork was assembled by reviewing upstream pull requests plus the Sir-Kam, codingforfun5435 and sign-river forks. Changes were selected individually rather than merging divergent forks wholesale.

Experimental RUNE binary-patching changes from upstream PR #112, sign-river's Chinese-first/remote-DLC-server additions, and codingforfun5435's broken boilerplate Conda workflow were intentionally not included in this stability-focused release.
