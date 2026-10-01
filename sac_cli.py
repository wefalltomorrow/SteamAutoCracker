import argparse
import json
import os
import sys

from sac_lib.restore import (
    discover_legacy_backups,
    load_manifest,
    remove_manifest,
    restore_entries,
)
from sac_lib.steam_install import (
    find_game_for_path,
    find_installed_games,
    validate_game_folder,
)
from sac_lib.steam_store import SteamStoreClient, SteamStoreError
from sac_lib.tool_updater import update_gbe_fork, update_steamless


def _print_json(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def _default_cache():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "tool_cache")


def cmd_list_installed(args):
    games = find_installed_games()
    if args.json:
        _print_json(games)
        return 0

    if not games:
        print("No installed Steam games found.")
        return 0

    width = max(len(game["appid"]) for game in games)
    for game in games:
        build = game.get("buildid") or "?"
        print(f'{game["appid"].rjust(width)}  {game["name"]}  [build {build}]')
        print(f'{" " * width}  {game["path"]}')
    return 0


def cmd_validate(args):
    result = validate_game_folder(args.path)
    manifest_game = find_game_for_path(args.path) if result["valid"] else None
    payload = {**result, "steam_manifest": manifest_game}

    if args.json:
        _print_json(payload)
    else:
        if not result["valid"]:
            print("INVALID:", result["error"])
            return 2
        print("Folder:", os.path.abspath(args.path))
        if manifest_game:
            print(
                f'Steam manifest: {manifest_game["name"]} '
                f'(AppID {manifest_game["appid"]}, build {manifest_game.get("buildid") or "unknown"})'
            )
        print("Steam API DLLs:", len(result["steam_api_files"]))
        for path in result["steam_api_files"]:
            print("  ", path)
        if result.get("warning"):
            print("WARNING:", result["warning"])
    return 0 if result["valid"] else 2


def cmd_metadata(args):
    client = SteamStoreClient(retry_max=args.retries, retry_delay=args.retry_delay)
    try:
        try:
            appid = int(args.query)
        except ValueError:
            match = client.search_app(args.query)
            if not match:
                print(f'No Steam Store match found for "{args.query}".', file=sys.stderr)
                return 3
            appid = match["appid"]

        metadata = client.game_metadata(appid)
    except SteamStoreError as exc:
        print(f"Steam metadata error: {exc}", file=sys.stderr)
        return 4

    _print_json(metadata)
    return 0


def cmd_restore(args):
    root = os.path.abspath(args.path)
    manifest = load_manifest(root)
    if manifest:
        entries = manifest["entries"]
        source = "restore manifest"
    else:
        entries = discover_legacy_backups(root)
        source = "legacy backup discovery"

    if not entries:
        print("No restorable SteamAutoCracker backups found.")
        return 0

    print(f"Found {len(entries)} restore entries using {source}.")
    for entry in entries:
        print(" ", entry)

    if not args.yes:
        print("Dry run only. Re-run with --yes to restore.")
        return 0

    result = restore_entries(root, entries)
    if manifest and not result["skipped"]:
        remove_manifest(root)
    _print_json(result)
    return 0 if not result["skipped"] else 5


def cmd_update_gbe(args):
    metadata = update_gbe_fork(os.path.abspath(args.cache))
    _print_json(metadata)
    return 0


def cmd_update_steamless(args):
    metadata = update_steamless(os.path.abspath(args.cache))
    _print_json(metadata)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="SteamAutoCracker best-of-all diagnostics and maintenance CLI"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    installed = sub.add_parser("list-installed", help="List installed Steam games")
    installed.add_argument("--json", action="store_true")
    installed.set_defaults(func=cmd_list_installed)

    validate = sub.add_parser("validate", help="Validate a selected game folder")
    validate.add_argument("path")
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=cmd_validate)

    metadata = sub.add_parser("metadata", help="Retrieve Steam metadata by AppID or title")
    metadata.add_argument("query")
    metadata.add_argument("--retries", type=int, default=5)
    metadata.add_argument("--retry-delay", type=float, default=2.0)
    metadata.set_defaults(func=cmd_metadata)

    restore = sub.add_parser("restore", help="Inspect or restore SAC backups")
    restore.add_argument("path")
    restore.add_argument("--yes", action="store_true", help="Actually perform the restore")
    restore.set_defaults(func=cmd_restore)

    gbe = sub.add_parser("update-gbe", help="Download and verify latest GBE_FORK")
    gbe.add_argument("--cache", default=_default_cache())
    gbe.set_defaults(func=cmd_update_gbe)

    steamless = sub.add_parser(
        "update-steamless", help="Download and verify latest Steamless-KR"
    )
    steamless.add_argument("--cache", default=_default_cache())
    steamless.set_defaults(func=cmd_update_steamless)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
