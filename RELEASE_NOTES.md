# SteamAutoCracker v2.4.1-wft.1

Small follow-up to v2.4.0.

## Steamless result handling

SAC now treats a **0/N Steamless result** as an incomplete DRM-removal run.

If Steamless was enabled, tried one or more executables, and unpacked none of them, the GUI shows:

`Steamless failed — DRM removal incomplete`

The log also explains that SteamStub or other launch checks may still be active and Steam may still require a valid license.

If restore data is available, the restore button changes to:

`Restore original files (recommended)`

Restore first before trying another method.

## Other changes

- Added a CI regression test for the 0/N Steamless case.
- Cleaned up the README, build docs, release notes and GUI wording.
- v2.4.0 features are otherwise unchanged.

## Downloads

- `Steam.Auto.Cracker.GUI.v2.4.1-wft.1.zip`
- `Steam.Auto.Cracker.GUI.v2.4.1-wft.1.zip.sha256`
