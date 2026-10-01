# Changelog

## 2.4.0-wft.1 — 2026-10-01

### Added

- Installed Steam game discovery from Steam registry/default locations, `libraryfolders.vdf`, and `appmanifest_*.acf`.
- Installed-games browser with game name, AppID, build ID, install path, filtering, one-click selection, and multi-select batch preflight.
- Automatic AppID matching when manually selecting a normal Steam game folder.
- Recursive Steam API DLL preflight validation and drive-root selection protection.
- Background-safe Steam Store client and Tk worker queue for non-blocking metadata/library/update operations.
- Verified optional GBE_FORK updater with release-size/SHA-256 validation, archive traversal protection, staging validation, and persistent cache.
- Verified optional Steamless-KR updater with safe ZIP extraction and persistent full release cache.
- In-place modern Steamless execution with captured exit code/stdout/stderr instead of temporarily moving game executables.
- Diagnostics/maintenance CLI for installed games, folder validation, Steam metadata, safe restores, and external tool updates.
- CI coverage for Steam VDF/appmanifest parsing, nested DLL validation, updater path traversal protection, cached tool resolution, and CLI startup.

### Changed

- Steam title/AppID metadata lookup now runs outside the Tk UI thread.
- GBE_FORK/Goldberg mode automatically prefers verified cached GBE_FORK x86/x64 DLLs when present while retaining the bundled fallback.
- Steamless automatically prefers a verified cached Steamless-KR CLI while retaining the bundled legacy fallback; modern-tool launch/unpack failures fall back automatically.
- Settings window exposes explicit manual update controls for maintained external tools.
- Release builds now also produce `steam_auto_cracker_cli.exe`.

### Preserved

- v2.3.1 safe restore manifests and `.sac-replaced` preservation.
- v2.3.0 issue #124 AppDetails defensive parsing.
- Fork-safe update behavior, themes, portable PE version parsing, CI and compiled-startup smoke tests.

### Source projects reviewed

- `SteamAutoCracks/Steam-auto-crack`: core/UI/CLI separation, maintained GBE_FORK/Steamless direction, verified updater concepts, asynchronous operations, and richer Steam metadata handling.
- `harryeffinpotter/Steam-Autocracker-GUI`: installed-library/appmanifest discovery, nested Steam API handling, root-drive protection, persistent UX patterns, and non-blocking long-running operations.

Upload/debrid/sharing pipelines and fragile hard-coded crack-size heuristics were intentionally excluded.

## 2.3.1-wft.1 — 2026-10-01

### Added

- **Restore original files** button available immediately after selecting a folder.
- Per-folder `.steamautocracker_restore.json` manifests for files changed by this release.
- Safe restore behavior that preserves the currently modified file as `.sac-replaced` before putting the original backup back.
- Conservative legacy-backup discovery for `steam_api.dll.bak`, `steam_api64.dll.bak`, and executable backups.
- CI regression tests for restore behavior, traversal protection, truthful completion messages, and source/runtime theme compatibility.
- Release pipeline smoke test that launches the compiled GUI and fails publishing if it exits during startup.

### Changed

- Completion reporting now describes the actual file operations performed instead of claiming launch success.
- Runs that contain incomplete executable processing report **Completed with warnings — launch not verified**.
- Existing restore manifests/backups block another modification pass until originals are restored.
- Existing known-good backup files are never overwritten.
- The ttkbootstrap constant compatibility shim is now present in the source as well as the compiled-build runtime hook.

### Restore behavior

- Manifest-backed restores can undo both replaced files and files created by this release.
- Modified files being replaced during restore are preserved using a unique `.sac-replaced` sidecar name.
- Legacy restore mode intentionally restores only confidently identified backup pairs; it does not guess at unrelated files created by older versions.

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
