# Changelog

## 2.4.1-wft.1 — 2026-10-01

### Fixed

- A Steamless run where every attempted executable fails now reports `Steamless failed — DRM removal incomplete` instead of a generic warning.
- The log explains that SteamStub or other launch checks may still be active and Steam may still require a valid license.
- When restore data exists after that result, the button changes to `Restore original files (recommended)`.
- Added a regression test for the 0/N Steamless result.

### Cleanup

- Rewrote the README, build docs and release notes in a shorter maintainer style.
- Cleaned up GUI labels/comments left over from earlier integration work.
- Reworded old PR descriptions/comments without rewriting Git history.

## 2.4.0-wft.1 — 2026-10-01

### Added

- Installed Steam game browser using Steam registry/default paths, `libraryfolders.vdf` and `appmanifest_*.acf`.
- AppID/build ID/path display, filtering, one-click selection and multi-select preflight.
- Automatic AppID matching for normal Steam install folders.
- Recursive Steam API DLL detection and root-drive selection protection.
- Background Steam Store/AppDetails/DLC lookup so network work does not block Tk.
- Optional GBE_FORK updater with size/SHA-256 checks, staged extraction and persistent cache.
- Optional Steamless-KR updater with safe extraction and persistent cache.
- In-place modern Steamless execution with exit-code/stdout/stderr reporting.
- Maintenance CLI for installed games, validation, metadata, restore and updater tasks.
- Crack-only ZIP mode.

### Changed

- GBE_FORK/Goldberg mode prefers verified cached GBE_FORK DLLs when available.
- Steamless prefers a verified cached Steamless-KR build and falls back to the bundled compatibility build.
- Release builds include `steam_auto_cracker_cli.exe`.
- GUI logging appends new lines instead of rewriting the whole log widget.

## 2.3.1-wft.1 — 2026-10-01

### Added

- `Restore original files` button.
- `.steamautocracker_restore.json` manifests.
- `.sac-replaced` preservation when restoring over a modified file.
- Legacy `.bak` backup discovery.
- Compiled-GUI startup smoke test in the release workflow.

### Changed

- Removed the unconditional success message.
- Added an operation summary and warning state when Steamless processing is incomplete.
- Existing restore data blocks another modification pass until originals are restored.

## 2.3.0-wft.1 — 2026-10-01

### Added

- Light, dark and black themes.
- Resizable GUI and scrollable monospaced log.
- Live Steam Store title search.
- Python 3.10/3.13 CI.
- PyInstaller release workflow with SHA-256 files.
- Portable PE version parsing with `pefile`.

### Fixed

- Steam AppDetails no longer crashes with `KeyError` when Steam omits the requested AppID key (upstream issue #124).
- AppDetails retries without `filters=basic` after an empty/missing-key response.
- Startup paths work correctly from PyInstaller builds.
- Rebuilt the first Windows release after fixing missing Tk constants in the `ttkbootstrap` alias.

### Changed

- Replaced the old `win32api` dependency with `pefile`.
- Fork update checks open this fork's release page instead of replacing the executable automatically.
