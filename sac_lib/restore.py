import json
import os
import shutil
from datetime import datetime, timezone

MANIFEST_NAME = ".steamautocracker_restore.json"
MANIFEST_VERSION = 1


def _root(root):
    return os.path.realpath(os.path.abspath(os.path.normpath(root)))


def _is_within(root_abs, candidate):
    try:
        return os.path.commonpath([root_abs, candidate]) == root_abs
    except ValueError:
        return False


def safe_join(root, relative_path):
    root_abs = _root(root)
    candidate = os.path.realpath(
        os.path.abspath(os.path.normpath(os.path.join(root_abs, relative_path)))
    )
    if not _is_within(root_abs, candidate):
        raise ValueError(f"Path escapes selected folder: {relative_path}")
    return candidate


def relpath(root, path):
    root_abs = _root(root)
    candidate = os.path.realpath(os.path.abspath(path))
    if not _is_within(root_abs, candidate):
        raise ValueError(f"Path escapes selected folder: {path}")
    return os.path.relpath(candidate, root_abs).replace("\\", "/")


def manifest_path(root):
    return os.path.join(_root(root), MANIFEST_NAME)


def load_manifest(root):
    path = manifest_path(root)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or data.get("version") != MANIFEST_VERSION:
        raise ValueError("Unsupported restore manifest")
    if not isinstance(data.get("entries"), list):
        raise ValueError("Invalid restore manifest")
    return data


def save_manifest(root, manifest):
    path = manifest_path(root)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temp_path, path)


def new_manifest():
    return {
        "version": MANIFEST_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "entries": [],
    }


def record_change(root, original_path, backup_path=None):
    manifest = load_manifest(root) or new_manifest()
    original_rel = relpath(root, original_path)
    backup_rel = relpath(root, backup_path) if backup_path else None

    entry = {
        "original": original_rel,
        "backup": backup_rel,
    }

    if entry not in manifest["entries"]:
        manifest["entries"].append(entry)
        save_manifest(root, manifest)

    return entry


def unique_sidecar(path, suffix=".sac-replaced"):
    candidate = path + suffix
    number = 2
    while os.path.exists(candidate):
        candidate = f"{path}{suffix}.{number}"
        number += 1
    return candidate


def discover_legacy_backups(root, steam_api_backup="steam_api.dll.bak",
                            steam_api64_backup="steam_api64.dll.bak",
                            exe_backup_suffix=".bak"):
    root_abs = _root(root)
    entries = []

    for current_root, _, files in os.walk(root_abs):
        file_set = set(files)

        pairs = [
            ("steam_api.dll", steam_api_backup),
            ("steam_api64.dll", steam_api64_backup),
        ]

        for original_name, backup_name in pairs:
            if not backup_name:
                continue
            if original_name in file_set and backup_name in file_set:
                entry = {
                    "original": relpath(root_abs, os.path.join(current_root, original_name)),
                    "backup": relpath(root_abs, os.path.join(current_root, backup_name)),
                }
                if entry not in entries:
                    entries.append(entry)

        if exe_backup_suffix:
            for name in files:
                if not name.lower().endswith(".exe"):
                    continue
                backup_name = name + exe_backup_suffix
                if backup_name in file_set:
                    entry = {
                        "original": relpath(root_abs, os.path.join(current_root, name)),
                        "backup": relpath(root_abs, os.path.join(current_root, backup_name)),
                    }
                    if entry not in entries:
                        entries.append(entry)

    return entries


def restore_entries(root, entries):
    restored = []
    removed_created = []
    preserved = []
    skipped = []

    for entry in entries:
        original_rel = entry.get("original")
        backup_rel = entry.get("backup")

        if not original_rel:
            skipped.append({"entry": entry, "reason": "missing original path"})
            continue

        try:
            original = safe_join(root, original_rel)
            backup = safe_join(root, backup_rel) if backup_rel else None
        except ValueError as exc:
            skipped.append({"entry": entry, "reason": str(exc)})
            continue

        if backup:
            if os.path.normcase(original) == os.path.normcase(backup):
                skipped.append({"entry": entry, "reason": "backup path equals original path"})
                continue

            if not os.path.isfile(backup):
                skipped.append({"entry": entry, "reason": "backup missing"})
                continue

            if os.path.exists(original):
                sidecar = unique_sidecar(original)
                shutil.move(original, sidecar)
                preserved.append(relpath(root, sidecar))

            os.makedirs(os.path.dirname(original), exist_ok=True)
            shutil.move(backup, original)
            restored.append(original_rel)
        else:
            if os.path.exists(original):
                sidecar = unique_sidecar(original)
                shutil.move(original, sidecar)
                preserved.append(relpath(root, sidecar))
                removed_created.append(original_rel)

    return {
        "restored": restored,
        "removed_created": removed_created,
        "preserved": preserved,
        "skipped": skipped,
    }


def remove_manifest(root):
    path = manifest_path(root)
    if os.path.isfile(path):
        os.remove(path)
