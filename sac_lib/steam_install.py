import os
import re


_TOKEN_RE = re.compile(r'"((?:\\.|[^"\\])*)"|([{}])')


def _unescape(value):
    return value.replace(r"\\", "\\").replace(r'\"', '"')


def parse_vdf(text):
    """Parse the simple KeyValues/ACF subset used by Steam library manifests."""
    tokens = []
    for match in _TOKEN_RE.finditer(text):
        if match.group(1) is not None:
            tokens.append(("string", _unescape(match.group(1))))
        else:
            tokens.append((match.group(2), match.group(2)))

    root = {}
    stack = [root]
    pending_key = None

    for kind, value in tokens:
        if kind == "string":
            if pending_key is None:
                pending_key = value
            else:
                stack[-1][pending_key] = value
                pending_key = None
        elif kind == "{":
            if pending_key is None:
                raise ValueError("Unexpected opening brace in VDF")
            child = {}
            stack[-1][pending_key] = child
            stack.append(child)
            pending_key = None
        elif kind == "}":
            if len(stack) == 1:
                raise ValueError("Unexpected closing brace in VDF")
            stack.pop()
            pending_key = None

    if len(stack) != 1:
        raise ValueError("Unclosed VDF object")
    return root


def parse_vdf_file(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return parse_vdf(handle.read())


def _norm(path):
    return os.path.realpath(os.path.abspath(os.path.expandvars(os.path.expanduser(path))))


def is_root_path(path):
    if not path:
        return False
    normalized = os.path.abspath(path)
    drive, tail = os.path.splitdrive(normalized)
    if drive and tail in ("\\", "/"):
        return True
    parent = os.path.dirname(normalized.rstrip("\\/"))
    return parent == normalized.rstrip("\\/")


def _registry_steam_paths():
    paths = []
    if os.name != "nt":
        return paths

    try:
        import winreg
    except ImportError:
        return paths

    candidates = [
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    ]

    for hive, key_name, value_name in candidates:
        try:
            with winreg.OpenKey(hive, key_name) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
            if value:
                paths.append(str(value))
        except OSError:
            pass

    return paths


def discover_steam_roots(extra_roots=None):
    candidates = []
    candidates.extend(_registry_steam_paths())

    for env_name in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(env_name)
        if base:
            candidates.append(os.path.join(base, "Steam"))

    candidates.extend([
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
    ])

    if extra_roots:
        candidates.extend(extra_roots)

    result = []
    seen = set()
    for path in candidates:
        normalized = _norm(path)
        key = os.path.normcase(normalized)
        if key in seen:
            continue
        seen.add(key)
        if os.path.isdir(os.path.join(normalized, "steamapps")):
            result.append(normalized)
    return result


def parse_libraryfolders(steam_root):
    libraries = [steam_root]
    vdf_path = os.path.join(steam_root, "steamapps", "libraryfolders.vdf")
    if not os.path.isfile(vdf_path):
        return libraries

    try:
        data = parse_vdf_file(vdf_path)
    except (OSError, ValueError):
        return libraries

    folders = data.get("libraryfolders", data)
    if isinstance(folders, dict):
        for key, value in folders.items():
            if not str(key).isdigit():
                continue
            path = value.get("path") if isinstance(value, dict) else value
            if path:
                libraries.append(str(path))

    unique = []
    seen = set()
    for path in libraries:
        normalized = _norm(path)
        key = os.path.normcase(normalized)
        if key in seen:
            continue
        seen.add(key)
        if os.path.isdir(os.path.join(normalized, "steamapps")):
            unique.append(normalized)
    return unique


def parse_appmanifest(path):
    data = parse_vdf_file(path)
    app_state = data.get("AppState", data)
    if not isinstance(app_state, dict):
        raise ValueError("Invalid appmanifest")

    def get(name, default=""):
        for key, value in app_state.items():
            if str(key).casefold() == name.casefold():
                return value
        return default

    return {
        "appid": str(get("appid", "")),
        "name": str(get("name", "")),
        "installdir": str(get("installdir", "")),
        "buildid": str(get("buildid", "")),
        "last_updated": str(get("LastUpdated", "")),
    }


def find_installed_games(extra_roots=None):
    games = []
    seen = set()

    for steam_root in discover_steam_roots(extra_roots):
        for library in parse_libraryfolders(steam_root):
            steamapps = os.path.join(library, "steamapps")
            common = os.path.join(steamapps, "common")
            try:
                names = os.listdir(steamapps)
            except OSError:
                continue

            for name in names:
                if not name.startswith("appmanifest_") or not name.endswith(".acf"):
                    continue

                manifest_path = os.path.join(steamapps, name)
                try:
                    info = parse_appmanifest(manifest_path)
                except (OSError, ValueError):
                    continue

                appid = info["appid"]
                install_dir = info["installdir"]
                if not appid or not install_dir:
                    continue

                game_path = os.path.join(common, install_dir)
                if not os.path.isdir(game_path):
                    continue

                key = (appid, os.path.normcase(_norm(game_path)))
                if key in seen:
                    continue
                seen.add(key)

                games.append({
                    **info,
                    "path": _norm(game_path),
                    "library": _norm(library),
                    "manifest": manifest_path,
                })

    games.sort(key=lambda game: (game["name"].casefold(), game["appid"]))
    return games


def find_steam_api_files(game_path):
    targets = {"steam_api.dll", "steam_api64.dll"}
    found = []
    if not os.path.isdir(game_path):
        return found

    for current_root, _, files in os.walk(game_path):
        for filename in files:
            if filename.casefold() in targets:
                found.append(os.path.join(current_root, filename))
    return found


def validate_game_folder(game_path):
    if not game_path or not os.path.isdir(game_path):
        return {
            "valid": False,
            "error": "Selected path is not a directory.",
            "steam_api_files": [],
        }

    if is_root_path(game_path):
        return {
            "valid": False,
            "error": "Selecting an entire drive root is not allowed.",
            "steam_api_files": [],
        }

    api_files = find_steam_api_files(game_path)
    return {
        "valid": True,
        "error": None,
        "steam_api_files": api_files,
        "warning": None if api_files else (
            "No steam_api.dll or steam_api64.dll was found under this folder. "
            "You can continue, but Steam API replacement may have nothing to modify."
        ),
    }
