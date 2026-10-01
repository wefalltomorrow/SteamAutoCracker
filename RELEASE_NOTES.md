# SteamAutoCracker v2.4.0-wft.1

Best-of-all maintenance release combining the strongest maintainable ideas from SteamAutoCracks/Steam-auto-crack and harryeffinpotter/Steam-Autocracker-GUI with the safer wefalltomorrow v2.3.x base.

## Highlights

- Browse detected installed Steam games instead of manually finding every folder/AppID, with filtering and multi-select batch preflight.
- Steam library discovery reads the normal Steam registry/default paths, `libraryfolders.vdf`, and `appmanifest_*.acf` files.
- Selecting a normal Steam install folder can auto-fill its AppID/build metadata.
- Recursive Steam API DLL validation catches nested game layouts and drive-root selection is rejected.
- Steam Store metadata work runs in a background worker rather than blocking Tk.
- Optional GBE_FORK updates are downloaded from the official release, verified against reported asset size/SHA-256, safely extracted, and cached beside SAC.
- Optional Steamless-KR updates use the same verified flow. Modern cached Steamless runs in-place and SAC records the actual CLI exit result. If .NET 9 is unavailable or the modern tool cannot unpack a target, SAC falls back to the bundled compatibility build.
- Compiled releases include a new `steam_auto_cracker_cli.exe` diagnostics/maintenance utility.
- Existing restore safety remains: manifests, traversal protection, no backup overwrite, preserved modified files, and truthful operation summaries.

## Maintenance CLI

`steam_auto_cracker_cli.exe` supports:

- `list-installed`
- `validate <path>`
- `metadata <appid-or-title>`
- `restore <path>` (dry-run by default; `--yes` performs it)
- `update-gbe`
- `update-steamless`

## External tool updates

External updates are manual and optional. SAC retains bundled fallbacks. Updated tools are stored in a persistent `tool_cache` folder next to the executable and do not overwrite original game files merely by being downloaded.

The updater verifies GitHub's asset size and SHA-256 digest when provided and rejects archive path traversal before extraction.

## What was intentionally not merged

This release does not import the unrelated upload/debrid/1fichier sharing subsystem, browser automation dependencies, or hard-coded emulator-DLL-size heuristics from other projects. The focus is core SteamAutoCracker reliability, maintainability and useful game-management improvements.

## Verification

CI verifies Python 3.10 and 3.13, source compilation, GUI/theme imports, restore safety, issue #124 parsing, Steam library discovery, nested API validation, updater extraction safety, CLI startup, PE parsing, and compiled Windows GUI startup before publication.

## Downloads

- `Steam.Auto.Cracker.GUI.v2.4.0-wft.1.zip` — Windows release containing GUI and maintenance CLI.
- `Steam.Auto.Cracker.GUI.v2.4.0-wft.1.zip.sha256` — SHA-256 checksum.

Built by GitHub Actions from the tagged `main` source.
