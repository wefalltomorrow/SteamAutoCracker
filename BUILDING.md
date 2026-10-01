# Building SteamAutoCracker

The maintained fork release is built on 64-bit Windows with Python and PyInstaller.

## Requirements

- Windows 10/11 or Windows Server
- Python 3.10+ (CI verifies 3.10 and 3.13)
- The dependencies in `requirements.txt`
- PyInstaller
- `py7zr` (installed through `requirements.txt`; used by optional GBE_FORK updates)

## Reproducible build

From the repository root:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --noconfirm --clean --onefile --windowed `
  --name steam_auto_cracker_gui `
  --icon icon_hashtag.ico `
  --add-data "sac_emu;sac_emu" `
  --add-data "Steamless_CLI;Steamless_CLI" `
  --add-data "icon_hashtag.ico;." `
  --collect-all tkinterdnd2 `
  --collect-all ttkbootstrap `
  --collect-all py7zr `
  steam_auto_cracker_gui.py
```

The executable is created at:

```
dist\steam_auto_cracker_gui.exe
```

The `--add-data` arguments are important because this fork resolves bundled emulator and Steamless resources through PyInstaller's `_MEIPASS` directory.

## Official fork builds

`.github/workflows/build-release.yml` performs the same build on GitHub's Windows runner, packages the EXE with README/LICENSE/CHANGELOG, generates a SHA-256 checksum, and can publish a GitHub release.

Release archives follow this naming scheme:

```
Steam.Auto.Cracker.GUI.v<version>.zip
Steam.Auto.Cracker.GUI.v<version>.zip.sha256
```

## Maintenance CLI build

The official release also builds the source maintenance CLI:

```powershell
pyinstaller --noconfirm --clean --onefile --console `
  --name steam_auto_cracker_cli `
  --collect-all py7zr `
  sac_cli.py
```

The result is `dist\steam_auto_cracker_cli.exe`. The release workflow smoke-tests `--help` before packaging.
