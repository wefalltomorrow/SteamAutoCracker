import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import requests


GITHUB_API = "https://api.github.com"
DEFAULT_HEADERS = {
    "User-Agent": "SteamAutoCracker-best-of-all",
    "Accept": "application/vnd.github+json",
}


class ToolUpdateError(RuntimeError):
    pass


def _safe_join(root, member):
    root = os.path.realpath(root)
    candidate = os.path.realpath(os.path.join(root, member))
    if os.path.commonpath([root, candidate]) != root:
        raise ToolUpdateError(f"Archive member escapes extraction root: {member}")
    return candidate


def _download(url, destination, expected_size=0, expected_digest=""):
    digest = expected_digest or ""
    if digest.lower().startswith("sha256:"):
        digest = digest.split(":", 1)[1].strip()

    hasher = hashlib.sha256()
    total = 0

    with requests.get(url, headers=DEFAULT_HEADERS, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(destination, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                hasher.update(chunk)
                total += len(chunk)

    if expected_size and total != int(expected_size):
        raise ToolUpdateError(
            f"Downloaded file size mismatch: expected {expected_size}, got {total}"
        )

    actual_digest = hasher.hexdigest()
    if digest and actual_digest.casefold() != digest.casefold():
        raise ToolUpdateError(
            f"SHA-256 mismatch: expected {digest}, got {actual_digest}"
        )

    return actual_digest


def _latest_release(repo):
    url = f"{GITHUB_API}/repos/{repo}/releases/latest"
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or not data.get("tag_name"):
        raise ToolUpdateError(f"Invalid latest-release response for {repo}")
    return data


def _pick_asset(release, preferred_names):
    assets = release.get("assets") or []
    by_name = {str(asset.get("name", "")): asset for asset in assets}
    for name in preferred_names:
        asset = by_name.get(name)
        if asset:
            return asset
    raise ToolUpdateError(
        "No compatible release asset found. Available assets: "
        + ", ".join(sorted(by_name))
    )


def _extract_zip(archive, destination):
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            _safe_join(destination, info.filename)
        zf.extractall(destination)


def _extract_7z(archive, destination):
    try:
        import py7zr
    except ImportError as exc:
        raise ToolUpdateError(
            "py7zr is required to inspect GBE_FORK archives safely"
        ) from exc

    # Inspect every member with Python first so an external extractor can never
    # be handed an archive containing ../ or absolute-path traversal entries.
    with py7zr.SevenZipFile(archive, mode="r") as zf:
        member_names = list(zf.getnames())

    for name in member_names:
        _safe_join(destination, name)

    extractors = []
    seven_zip_candidates = []
    for command in ("7z", "7zz", "7za"):
        executable = shutil.which(command)
        if executable:
            seven_zip_candidates.append(executable)

    if os.name == "nt":
        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(env_name)
            if base:
                candidate = os.path.join(base, "7-Zip", "7z.exe")
                if os.path.isfile(candidate):
                    seven_zip_candidates.append(candidate)

    seen_extractors = set()
    for executable in seven_zip_candidates:
        key = os.path.normcase(os.path.abspath(executable))
        if key in seen_extractors:
            continue
        seen_extractors.add(key)
        extractors.append(
            (
                executable,
                [executable, "x", archive, f"-o{destination}", "-y", "-bd"],
            )
        )

    # Windows 10/11 ship bsdtar as tar.exe; libarchive can read 7z/BCJ2.
    for command in ("tar", "bsdtar"):
        tar_exe = shutil.which(command)
        if not tar_exe:
            continue
        key = os.path.normcase(os.path.abspath(tar_exe))
        if key in seen_extractors:
            continue
        seen_extractors.add(key)
        extractors.append(
            (
                tar_exe,
                [tar_exe, "-xf", archive, "-C", destination],
            )
        )

    last_error = None
    for executable, args in extractors:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=180,
            shell=False,
        )
        if completed.returncode == 0:
            return
        last_error = (
            completed.stderr.strip()
            or completed.stdout.strip()
            or f"{os.path.basename(executable)} exited {completed.returncode}"
        )

    # py7zr remains a final fallback for archives that do not use unsupported
    # filters. Current GBE_FORK releases use BCJ2, so Windows normally reaches
    # this only when neither 7-Zip nor Windows tar is available.
    try:
        with py7zr.SevenZipFile(archive, mode="r") as zf:
            zf.extractall(destination)
        return
    except Exception as exc:
        detail = last_error or str(exc)
        raise ToolUpdateError(
            "Could not extract the GBE_FORK 7z archive. "
            "A native 7-Zip-compatible extractor is required for its BCJ2 filter. "
            f"Last error: {detail}"
        ) from exc


def _find_file(root, filename, required_parts=()):
    filename = filename.casefold()
    required = [part.casefold() for part in required_parts]
    matches = []

    for path in Path(root).rglob("*"):
        if not path.is_file() or path.name.casefold() != filename:
            continue
        parts = [part.casefold() for part in path.parts]
        if all(part in parts for part in required):
            matches.append(path)

    if not matches:
        return None

    matches.sort(key=lambda path: len(path.parts))
    return str(matches[0])


def _write_metadata(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temp, path)


def gbe_cache_dir(cache_root):
    return os.path.join(cache_root, "gbe_fork")


def steamless_cache_dir(cache_root):
    return os.path.join(cache_root, "steamless")


def _read_metadata(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def get_cached_gbe_metadata(cache_root):
    return _read_metadata(os.path.join(gbe_cache_dir(cache_root), "metadata.json"))


def get_cached_steamless_metadata(cache_root):
    return _read_metadata(os.path.join(steamless_cache_dir(cache_root), "metadata.json"))


def get_cached_gbe_dll(cache_root, filename):
    path = os.path.join(gbe_cache_dir(cache_root), filename)
    return path if os.path.isfile(path) else None


def get_cached_steamless_executable(cache_root):
    metadata = get_cached_steamless_metadata(cache_root)
    if not metadata:
        return None
    exe = metadata.get("executable")
    if exe:
        path = os.path.join(steamless_cache_dir(cache_root), exe)
        if os.path.isfile(path):
            return path
    return None


def update_gbe_fork(cache_root):
    release = _latest_release("Detanup01/gbe_fork")
    asset = _pick_asset(
        release,
        ["emu-win-release-vs26.7z", "emu-win-release-vs22.7z"],
    )

    target = gbe_cache_dir(cache_root)
    staging = target + ".staging"
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory(prefix="sac-gbe-") as temp:
            archive = os.path.join(temp, asset["name"])
            digest = _download(
                asset["browser_download_url"],
                archive,
                asset.get("size") or 0,
                asset.get("digest") or "",
            )
            extracted = os.path.join(temp, "extracted")
            os.makedirs(extracted)
            _extract_7z(archive, extracted)

            dll32 = _find_file(extracted, "steam_api.dll", ("regular", "x86"))
            dll64 = _find_file(extracted, "steam_api64.dll", ("regular", "x64"))
            if not dll32 or not dll64:
                raise ToolUpdateError(
                    "GBE_FORK release did not contain regular x86/x64 Steam API DLLs"
                )

            shutil.copy2(dll32, os.path.join(staging, "steam_api.dll"))
            shutil.copy2(dll64, os.path.join(staging, "steam_api64.dll"))

        metadata = {
            "repo": "Detanup01/gbe_fork",
            "version": release["tag_name"],
            "asset": asset["name"],
            "asset_sha256": digest,
        }
        _write_metadata(os.path.join(staging, "metadata.json"), metadata)

        shutil.rmtree(target, ignore_errors=True)
        os.replace(staging, target)
        return metadata
    finally:
        if os.path.isdir(staging):
            shutil.rmtree(staging, ignore_errors=True)


def update_steamless(cache_root):
    release = _latest_release("K0oRui/Steamless-KR")
    tag = release["tag_name"]
    asset_name = f"Steamless-{tag}-windows.zip"
    asset = _pick_asset(release, [asset_name])

    target = steamless_cache_dir(cache_root)
    staging = target + ".staging"
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory(prefix="sac-steamless-") as temp:
            archive = os.path.join(temp, asset["name"])
            digest = _download(
                asset["browser_download_url"],
                archive,
                asset.get("size") or 0,
                asset.get("digest") or "",
            )
            _extract_zip(archive, staging)

        executable = (
            _find_file(staging, "Steamless.CLI.exe")
            or _find_file(staging, "Steamless.exe")
        )
        if not executable:
            raise ToolUpdateError(
                "Steamless release did not contain a Windows executable"
            )

        relative_executable = os.path.relpath(executable, staging)
        metadata = {
            "repo": "K0oRui/Steamless-KR",
            "version": release["tag_name"],
            "asset": asset["name"],
            "asset_sha256": digest,
            "executable": relative_executable,
        }
        _write_metadata(os.path.join(staging, "metadata.json"), metadata)

        shutil.rmtree(target, ignore_errors=True)
        os.replace(staging, target)
        return metadata
    finally:
        if os.path.isdir(staging):
            shutil.rmtree(staging, ignore_errors=True)

