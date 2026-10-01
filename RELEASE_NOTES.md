# SteamAutoCracker v2.3.1-wft.1

Maintenance release focused on reliable recovery, preservation of originals, and truthful run results.

## Highlights

- Adds a **Restore original files** button that works without needing to repeat the Steam metadata lookup.
- Saves a restore manifest whenever this release backs up or creates files.
- Never destroys the current modified file during restore; it is preserved with a `.sac-replaced` suffix first.
- Detects common backup pairs from older builds so existing folders can be recovered even when no manifest exists.
- Refuses to overwrite a known-good backup or perform another modification pass while restore data is present.
- Removes the misleading unconditional “success” result.
- Shows a detailed operation summary and reports **Completed with warnings — launch not verified** when an executable stage does not complete.
- Keeps the v2.3.0 fixes for Steam AppDetails issue #124, live Steam Store lookup, themes, portable PE parsing, PyInstaller paths, and fork-safe update checks.
- Keeps the compiled startup fix for missing ttkbootstrap/Tk constants, and now also applies that compatibility directly to source runs.

## Restore safety

For manifest-backed changes, the release records both:

- files whose originals were moved to backups; and
- files newly created by the application.

When restoring a replaced file, the active modified copy is renamed to a unique `.sac-replaced` sidecar before the known-good backup is moved back into place.

For folders changed by older releases that have no manifest, legacy restore mode only uses confidently matched backup pairs. It deliberately does not delete other files based on guesses.

## Verification

The release CI checks:

- Python 3.10 and 3.13 source compilation;
- GUI/theme dependency imports;
- ttkbootstrap compatibility constants;
- PE version parsing;
- Steam AppDetails issue #124 regression;
- restore-manifest round trip;
- preservation of modified files during restore;
- path-traversal rejection; and
- absence of the old unconditional success message.
- compiled Windows GUI startup smoke test before publishing the release asset.

## Downloads

- `Steam.Auto.Cracker.GUI.v2.3.1-wft.1.zip` — compiled 64-bit Windows release.
- `Steam.Auto.Cracker.GUI.v2.3.1-wft.1.zip.sha256` — SHA-256 checksum.

The Windows release is built from the tagged `main` source by GitHub Actions.
