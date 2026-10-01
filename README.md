# SteamAutoCracker

[![CI](https://github.com/wefalltomorrow/SteamAutoCracker/actions/workflows/ci.yml/badge.svg)](https://github.com/wefalltomorrow/SteamAutoCracker/actions/workflows/ci.yml)
![Downloads](https://img.shields.io/github/downloads/wefalltomorrow/SteamAutoCracker/total?label=Downloads)
![Latest release](https://img.shields.io/github/downloads/wefalltomorrow/SteamAutoCracker/latest/total?label=Latest%20release)
![Stars](https://img.shields.io/github/stars/wefalltomorrow/SteamAutoCracker?label=Stars)

Maintained fork of [BigBoiCJ/SteamAutoCracker](https://github.com/BigBoiCJ/SteamAutoCracker).

This keeps the original Python/Tkinter project and adds fixes and features from upstream PRs and other active forks.

## Download

Get the latest Windows build from [Releases](https://github.com/wefalltomorrow/SteamAutoCracker/releases/latest).

The ZIP contains:

- `steam_auto_cracker_gui.exe`
- `steam_auto_cracker_cli.exe`
- README, changelog and license

## Features

- Steam API replacement/config generation for ALI213, Goldberg/GBE_FORK and CreamAPI.
- Steamless support for SteamStub-protected executables.
- Installed Steam game browser using `libraryfolders.vdf` and `appmanifest_*.acf`.
- Automatic AppID/build matching for normal Steam install folders.
- Recursive `steam_api.dll` / `steam_api64.dll` detection.
- Live Steam Store title/AppID lookup without a Steam Web API key.
- Optional GBE_FORK and Steamless-KR updates from their official GitHub releases.
- Restore manifests for files changed by SAC.
- Crack-only ZIP mode that leaves the selected game folder alone.
- Light, dark and black themes.
- CLI tools for installed-game discovery, metadata checks, restore and updater tasks.

## v2.4.1

v2.4.1 fixes the result shown when Steamless fails to unpack every executable it tried.

Before this release, a 0/N Steamless result could end with a generic warning after the Steam API files had already been replaced. That made the run look more complete than it was.

Now SAC reports:

`Steamless failed — DRM removal incomplete`

It also explains that SteamStub or other launch checks may still be active, warns that Steam may still require a valid license, and changes the restore button to:

`Restore original files (recommended)`

Restore first before trying another method.

## Installed Steam games

Click **Installed Steam games** to scan detected Steam libraries.

SAC reads:

- Steam registry/default install paths
- `steamapps/libraryfolders.vdf`
- `steamapps/appmanifest_*.acf`

The browser shows game name, AppID, build ID and path. Selecting a game fills the folder and AppID automatically.

You can also select a folder manually or drag one into the window.

## External tool updates

Settings has manual update buttons for:

- [GBE_FORK](https://github.com/Detanup01/gbe_fork)
- [Steamless-KR](https://github.com/K0oRui/Steamless-KR)

Downloads go into `tool_cache` next to SAC. The updater checks the release asset size and SHA-256 digest when GitHub provides one, validates the extracted files, and keeps the bundled copies as fallbacks.

Steamless-KR currently needs .NET 9. If the updated build cannot run, SAC falls back to the bundled compatibility version.

## Restore

When SAC changes or creates files it writes `.steamautocracker_restore.json` in the selected game folder.

**Restore original files**:

- restores known backups;
- removes SAC-created files from their active paths;
- moves the current modified copy aside with a `.sac-replaced` suffix instead of deleting it;
- rejects restore entries that escape the selected game folder.

SAC also has limited support for older `.bak` backups created before restore manifests existed.

## Crack-only ZIP

In Settings, set **Crack approach** to:

`Build a crack-only ZIP beside SteamAutoCracker`

This builds a ZIP using the selected emulator/config without writing to the game folder.

## CLI

The Windows release includes `steam_auto_cracker_cli.exe`. Source users can run `python sac_cli.py`.

```text
steam_auto_cracker_cli.exe list-installed
steam_auto_cracker_cli.exe validate "D:\SteamLibrary\steamapps\common\Example Game"
steam_auto_cracker_cli.exe metadata 123456
steam_auto_cracker_cli.exe restore "D:\Games\Example"
steam_auto_cracker_cli.exe restore "D:\Games\Example" --yes
steam_auto_cracker_cli.exe update-gbe
steam_auto_cracker_cli.exe update-steamless
```

Restore is a dry run unless `--yes` is supplied.

## Requirements

### Compiled build

- 64-bit Windows
- Internet connection for Steam metadata and optional tool updates

### Running from source

- Python 3.10+
- dependencies from `requirements.txt`
- tkinter (normally included with Windows Python)

```powershell
python -m pip install -r requirements.txt
python steam_auto_cracker_gui.py
```

CI runs on Python 3.10 and 3.13.

## Building

See [BUILDING.md](BUILDING.md).

Release builds are made with PyInstaller on GitHub Actions. The workflow builds the GUI and CLI, smoke-tests both, packages them, and writes a SHA-256 file.

## Notes

- Some DLC needs extra game files. SAC only handles configuration/unlock data; it does not download missing DLC files.
- Replacing Steam API files does not guarantee the game will launch.
- If Steamless fails to unpack all attempted executables, restore the original files before trying another method.

## Privacy

SAC contacts Steam's public Store endpoints for game metadata.

The update checker uses this fork's public GitHub release metadata. Automatic update checks are off by default.

There is no analytics or telemetry. Local config/log/cache files are stored beside the executable or source checkout.

PyInstaller one-file builds temporarily extract files to the normal `_MEI...` temp directory while running.

## Credits

Original project: [BigBoiCJ/SteamAutoCracker](https://github.com/BigBoiCJ/SteamAutoCracker)

This fork also reviewed or borrowed ideas from:

- [Sir-Kam/SteamAutoCracker](https://github.com/Sir-Kam/SteamAutoCracker)
- [sign-river/SteamAutoCracker](https://github.com/sign-river/SteamAutoCracker)
- [SteamAutoCracks/Steam-auto-crack](https://github.com/SteamAutoCracks/Steam-auto-crack)
- [harryeffinpotter/Steam-Autocracker-GUI](https://github.com/harryeffinpotter/Steam-Autocracker-GUI)

External projects used/supported:

- [Steamless](https://github.com/atom0s/Steamless)
- [Steamless-KR](https://github.com/K0oRui/Steamless-KR)
- [GBE_FORK](https://github.com/Detanup01/gbe_fork)
- ALI213
- CreamAPI

See [CHANGELOG.md](CHANGELOG.md) for release history.
