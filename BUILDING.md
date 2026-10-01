# Building SteamAutoCracker

The release workflow builds two Windows executables with PyInstaller:

- `steam_auto_cracker_gui.exe`
- `steam_auto_cracker_cli.exe`

## Requirements

- Windows
- Python 3.10+
- dependencies from `requirements.txt`
- PyInstaller

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

## GUI

Run from the repository root:

```powershell
pyinstaller --noconfirm --clean --onefile --windowed `
  --name steam_auto_cracker_gui `
  --icon icon_hashtag.ico `
  --add-data "sac_emu;sac_emu" `
  --add-data "Steamless_CLI;Steamless_CLI" `
  --add-data "icon_hashtag.ico;." `
  --collect-all tkinterdnd2 `
  --collect-all ttkbootstrap `
  --runtime-hook ".github/runtime_hooks/ttkbootstrap_tk_constants.py" `
  steam_auto_cracker_gui.py
```

Output: `dist\steam_auto_cracker_gui.exe`

## CLI

```powershell
pyinstaller --noconfirm --clean --onefile --console `
  --name steam_auto_cracker_cli `
  sac_cli.py
```

Output: `dist\steam_auto_cracker_cli.exe`

## Release workflow

`.github/workflows/build-release.yml` installs dependencies, builds both executables, smoke-tests the CLI, launches the compiled GUI to catch startup crashes, creates the ZIP/checksum, uploads the artifact and publishes from `publish-v*` branches.

The ZIP contains both executables plus README, CHANGELOG and LICENSE.
