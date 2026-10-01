import os
import re
import shutil
import tempfile
import zipfile


_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


def safe_filename(value, fallback="game"):
    value = _INVALID_FILENAME.sub("_", str(value or "")).strip(" ._")
    return value or fallback


def _render_text(content, replacements):
    for old, new in replacements.items():
        content = content.replace(old, str(new))
    return content


def build_crack_only_archive(
    game_root,
    game_name,
    appid,
    template_root,
    dll_locations,
    replacements,
    output_dir,
    source_overrides=None,
):
    """Build a crack-only ZIP without modifying the selected game directory.

    Each detected Steam API directory receives a copy of the selected crack
    template at its path relative to game_root. Text config files receive the
    same SAC_* placeholder replacements used by the normal GUI flow.
    """
    game_root = os.path.realpath(os.path.abspath(game_root))
    template_root = os.path.realpath(os.path.abspath(template_root))
    output_dir = os.path.realpath(os.path.abspath(output_dir))
    source_overrides = source_overrides or {}

    if not os.path.isdir(game_root):
        raise ValueError("Game root does not exist")
    if not os.path.isdir(template_root):
        raise ValueError("Crack template does not exist")
    if not dll_locations:
        raise ValueError("No Steam API locations were detected")

    os.makedirs(output_dir, exist_ok=True)
    stem = safe_filename(f"{game_name} - {appid}")
    archive_path = os.path.join(output_dir, f"{stem}.zip")

    with tempfile.TemporaryDirectory(prefix="sac-crack-only-") as staging:
        package_root = os.path.join(staging, stem)
        os.makedirs(package_root, exist_ok=True)

        if isinstance(dll_locations, dict):
            location_items = sorted(dll_locations.items())
        else:
            location_items = [(path, "") for path in sorted(set(dll_locations))]

        for dll_location, api_version in location_items:
            dll_location = os.path.realpath(os.path.abspath(dll_location))
            if os.path.commonpath([game_root, dll_location]) != game_root:
                raise ValueError("Steam API location escapes selected game root")

            location_replacements = dict(replacements)
            location_replacements["SAC_APIVersion"] = str(api_version or "")

            location_rel = os.path.relpath(dll_location, game_root)
            if location_rel == ".":
                location_rel = ""

            for current_root, dirs, files in os.walk(template_root):
                template_rel = os.path.relpath(current_root, template_root)
                if template_rel == ".":
                    template_rel = ""

                target_dir = os.path.join(package_root, location_rel, template_rel)
                os.makedirs(target_dir, exist_ok=True)

                for directory in dirs:
                    os.makedirs(os.path.join(target_dir, directory), exist_ok=True)

                for filename in files:
                    source = source_overrides.get(filename)
                    if not source:
                        source = os.path.join(current_root, filename)

                    target = os.path.join(target_dir, filename)
                    extension = os.path.splitext(filename)[1].casefold()
                    if extension in {".txt", ".ini", ".cfg"}:
                        try:
                            with open(source, "r", encoding="utf-8") as handle:
                                data = handle.read()
                            data = _render_text(data, location_replacements)
                            with open(target, "w", encoding="utf-8") as handle:
                                handle.write(data)
                            continue
                        except UnicodeDecodeError:
                            pass

                    shutil.copy2(source, target)

        with zipfile.ZipFile(
            archive_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for current_root, _, files in os.walk(package_root):
                for filename in files:
                    path = os.path.join(current_root, filename)
                    arcname = os.path.relpath(path, staging)
                    archive.write(path, arcname)

    return archive_path
