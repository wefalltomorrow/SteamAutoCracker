import os
import sys
import traceback

try: # Handles Python errors to write them to a log file so they can be reported and fixed more easily.
    ## Replaced by 'ttkbootstrap' for [easier] themes
    #import tkinter as tk
    from tkinter import ttk, filedialog, font, messagebox
    from tkinterdnd2 import DND_FILES, TkinterDnD

    ## Used for theming/coloring configuration for the UI
    import ttkbootstrap
    import ttkbootstrap as tk

    # ttkbootstrap provides Tk/ttk widgets but not classic tkinter constants
    # such as BOTH/END/NORMAL at its package root. Keep the historical `tk`
    # alias working for source runs as well as compiled builds.
    _TK_COMPAT_CONSTANTS = {
        "END": "end",
        "NORMAL": "normal",
        "DISABLED": "disabled",
        "LEFT": "left",
        "RIGHT": "right",
        "BOTH": "both",
        "Y": "y",
    }
    for _constant_name, _constant_value in _TK_COMPAT_CONSTANTS.items():
        if not hasattr(tk, _constant_name):
            setattr(tk, _constant_name, _constant_value)

    import requests
    import configparser
    import subprocess
    from sac_lib.get_file_version import GetFileVersion
    from sac_lib.steam_store import (
        SteamStoreClient,
        SteamStoreError,
    )
    from sac_lib.steam_install import (
        find_game_for_path,
        find_installed_games,
        validate_game_folder,
    )
    from sac_lib.background import run_background
    from sac_lib.package_builder import build_crack_only_archive
    from sac_lib.run_result import classify_run_result
    from sac_lib.steamless_runner import run_modern_steamless
    from sac_lib.tool_updater import (
        get_cached_gbe_dll,
        get_cached_gbe_metadata,
        get_cached_steamless_executable,
        get_cached_steamless_metadata,
        update_gbe_fork,
        update_steamless,
    )
    from sac_lib.restore import (
        discover_legacy_backups,
        load_manifest,
        manifest_path,
        record_change,
        remove_manifest,
        restore_entries,
    )
    import shutil
    from time import sleep
    from sys import exit
    import re
    import webbrowser
    import typing

    VERSION = "2.4.1-wft.1"

    RETRY_DELAY = 15 # Delay in seconds before retrying a failed request. (default, can be modified in config.ini)
    RETRY_MAX = 30 # Number of failed tries (includes the first try) after which SAC will stop trying and quit. (default, can be modified in config.ini)

    folder_path = ""
    appID = 0
    gameSearchDone = False

    EXTS_TO_REPLACE = (".txt", ".ini", ".cfg")

    DEFAULT_REQUEST_HEADERS = {
        "User-Agent": f"SteamAutoCracker/{VERSION} (+https://github.com/wefalltomorrow/SteamAutoCracker)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    GITHUB_RAWHOST = "raw.githubusercontent.com"
    GITHUB_APIHOST = "api.github.com"
    GITHUB_ACCREPOSTR = "BigBoiCJ/SteamAutoCracker"
    FORK_REPO = "wefalltomorrow/SteamAutoCracker"
    FORK_LATESTRELEASEJSON = f"https://{GITHUB_APIHOST}/repos/{FORK_REPO}/releases/latest"

    def get_app_dir():
        """Directory for writable user files such as config and logs."""
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def get_resource_path(relative_path):
        """Resolve bundled read-only resources in source and PyInstaller builds."""
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def get_user_path(filename):
        return os.path.join(get_app_dir(), filename)

    def get_tool_cache_dir():
        path = os.path.join(get_app_dir(), "tool_cache")
        os.makedirs(path, exist_ok=True)
        return path

    def version_key(value):
        parts = [int(part) for part in re.findall(r"\d+", str(value or ""))]
        return tuple(parts or [0])

    def OnTkinterError(exc, val, tb):
        # Handle Tkinter Python errors
        print("\n[!!!] A Tkinter Python error occurred! Writing the error to the error_tkinter.log file.\n---")
        with open(get_user_path("error_tkinter.log"), "w", encoding="utf-8") as errorFile:
            errorFile.write(f"SteamAutoCracker GUI v{VERSION}\n---\nA Tkinter Python error occurred!\nPlease report it on GitHub or cs.rin.ru\nMake sure to blank any personal detail.\nNOTE: '_tkinter.TclError: invalid command name' errors are normal if you closed the window while SAC was busy. In that case, you should not report the issue and just ignore it.\n---\n\n")
            traceback.print_exc(file=errorFile)
        traceback.print_exc()
        print("---\nError written to error_tkinter.log, please report it on GitHub or cs.rin.ru\nMake sure to blank any personal detail.")

        try:
            update_logs("[!!!] A Tkinter Python error occurred! The error has written to error_tkinter.log, please report it on GitHub or cs.rin.ru\nMake sure to blank any personal detail.")
        except Exception:
            pass

    class SACRequest:
        def __init__(self, url: str, name: str = "Unnamed", params: dict = None, headers: dict = None):
            self.url = url
            self.params = params
            self.headers = headers or DEFAULT_REQUEST_HEADERS
            self.tries = 0
            self.name = name
            self.DoRequest()

        def DoRequest(self):
            max_tries = int(config["Advanced"]["RetryMax"])
            retry_delay = int(config["Advanced"]["RetryDelay"])
            last_error = None

            for attempt in range(1, max_tries + 1):
                self.tries = attempt
                try:
                    req = requests.get(
                        self.url,
                        params=self.params,
                        headers=self.headers,
                        timeout=10,
                    )
                    req.raise_for_status()
                    self.req = req
                    return
                except requests.RequestException as exc:
                    last_error = exc
                    if attempt >= max_tries:
                        break

                    update_logs(
                        "- " + self.name + " request failed, retrying in "
                        + str(retry_delay) + "s... ("
                        + str(attempt) + "/" + str(max_tries) + " tries)"
                    )
                    root.update()
                    sleep(retry_delay)

            update_logs(
                "[!] Connection failed after " + str(max_tries)
                + " tries. Are you connected to the Internet? Is Steam online?\n"
                + "If you are being rate limited, try increasing RetryDelay and RetryMax."
            )
            raise Exception(
                f"SACRequest: {self.name} failed after {max_tries} tries"
            ) from last_error

    def _apply_folder_selection(folder_path_temp, suggested_entry=None):
        global folder_path
        global last_selected_folder

        validation = validate_game_folder(folder_path_temp)
        if not validation["valid"]:
            update_logs("\n[!] " + validation["error"])
            try:
                messagebox.showerror("Invalid game folder", validation["error"])
            except Exception:
                pass
            return False

        folder_path = os.path.abspath(folder_path_temp)
        last_selected_folder = os.path.dirname(folder_path)
        config["Preferences"]["last_selected_folder"] = last_selected_folder
        UpdateConfig()

        folder_name = os.path.basename(folder_path)
        update_logs(f"\nSelected folder: {folder_path}")

        api_files = validation.get("steam_api_files") or []
        if api_files:
            update_logs(
                f"\n- Found {len(api_files)} Steam API DLL"
                + ("s" if len(api_files) != 1 else "")
                + " under the selected folder."
            )
        elif validation.get("warning"):
            update_logs("\n[!] " + validation["warning"])

        selectedFolderLabel.config(text=f"Selected folder:\n{folder_path}")
        selectedFolderLabel.pack()
        restoreFilesButton.config(text="Restore original files")
        restoreFilesButton.pack(pady=(0, 10))
        frameGame2.pack()

        gameNameEntry.delete(0, tk.END)
        if suggested_entry:
            entry_value = suggested_entry
        else:
            manifest_game = find_game_for_path(folder_path)
            entry_value = manifest_game["appid"] if manifest_game else folder_name
            if manifest_game:
                update_logs(
                    f'\n- Matched selected folder to Steam AppID {manifest_game["appid"]} '
                    f'({manifest_game["name"]}, build {manifest_game.get("buildid") or "unknown"}).'
                )
        gameNameEntry.insert(0, entry_value)

        if gameSearchDone:
            frameCrack2.pack()
        return True

    def handle_folder_selection(event=None):
        global folder_path
        global last_selected_folder

        def reset_folder_selection_ui():
            selectedFolderLabel.config(text="")
            selectedFolderLabel.pack_forget()
            restoreFilesButton.pack_forget()
            frameGame2.pack_forget()
            frameCrack2.pack_forget()

        if event:
            folder_path_temp = event.data.strip("{}").replace("\\", "/")
        else:
            initial_dir = "/"
            last_selected_folder = config["Preferences"].get("last_selected_folder", "")
            if last_selected_folder and os.path.isdir(last_selected_folder):
                initial_dir = last_selected_folder
            folder_path_temp = filedialog.askdirectory(initialdir=initial_dir)
            if isinstance(folder_path_temp, tuple):
                folder_path_temp = folder_path_temp[0] if folder_path_temp else ""

        if folder_path_temp and _apply_folder_selection(folder_path_temp):
            return

        if not folder_path_temp:
            update_logs("\nNo folder selected")
        folder_path = ""
        reset_folder_selection_ui()

    def BrowseInstalledGames():
        installedGamesButton.config(state=tk.DISABLED)
        installedGamesStatus.config(text="Scanning Steam libraries...")

        def worker():
            return find_installed_games()

        def success(games):
            installedGamesStatus.config(text=f"Found {len(games)} installed Steam games")
            if not games:
                messagebox.showinfo(
                    "Installed Steam games",
                    "No installed Steam games were found in the detected Steam libraries.",
                )
                return

            top = tk.Toplevel(root)
            top.title(f"SteamAutoCracker GUI v{VERSION} - Installed Steam games")
            top.geometry("900x560")
            top.minsize(700, 420)

            ttk.Label(top, text="Installed Steam games", font=FONT2, padding=6).pack(
                anchor="center", pady=(8, 0)
            )

            filter_var = tk.StringVar()
            filter_entry = tk.Entry(top, textvariable=filter_var, font=FONT_APP_ENTRY)
            filter_entry.pack(fill="x", padx=12, pady=(8, 8))

            frame = ttk.Frame(top)
            frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

            columns = ("name", "appid", "build", "path")
            tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
            tree.heading("name", text="Game")
            tree.heading("appid", text="AppID")
            tree.heading("build", text="Build ID")
            tree.heading("path", text="Install path")
            tree.column("name", width=230)
            tree.column("appid", width=80, anchor="center")
            tree.column("build", width=90, anchor="center")
            tree.column("path", width=430)

            yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=yscroll.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            yscroll.pack(side=tk.RIGHT, fill=tk.Y)

            item_map = {}

            def populate(*_):
                query = filter_var.get().strip().casefold()
                for item in tree.get_children():
                    tree.delete(item)
                item_map.clear()

                for game in games:
                    haystack = (
                        game["name"] + " " + game["appid"] + " " + game["path"]
                    ).casefold()
                    if query and query not in haystack:
                        continue
                    item = tree.insert(
                        "",
                        "end",
                        values=(
                            game["name"],
                            game["appid"],
                            game.get("buildid", ""),
                            game["path"],
                        ),
                    )
                    item_map[item] = game

            def choose(*_):
                selected = tree.selection()
                if not selected:
                    return
                game = item_map.get(selected[0])
                if not game:
                    return
                if _apply_folder_selection(game["path"], game["appid"]):
                    update_logs(
                        f'\n- Selected installed Steam game "{game["name"]}" '
                        f'(AppID {game["appid"]}, build {game.get("buildid") or "unknown"}).'
                    )
                    top.destroy()

            def preflight_selected():
                selected = tree.selection()
                games_to_check = [
                    item_map[item] for item in selected if item in item_map
                ]
                if not games_to_check:
                    messagebox.showinfo(
                        "Batch preflight",
                        "Select one or more installed games first.",
                        parent=top,
                    )
                    return

                def worker():
                    results = []
                    for game in games_to_check:
                        validation = validate_game_folder(game["path"])
                        results.append((game, validation))
                    return results

                def success(results):
                    lines = []
                    valid_count = 0
                    api_count = 0
                    for game, validation in results:
                        if validation["valid"]:
                            valid_count += 1
                        count = len(validation.get("steam_api_files") or [])
                        api_count += count
                        status = (
                            f"{count} Steam API DLL(s)"
                            if validation["valid"]
                            else validation["error"]
                        )
                        lines.append(
                            f'{game["name"]} (AppID {game["appid"]}): {status}'
                        )

                    summary = (
                        f"{valid_count}/{len(results)} folders passed validation; "
                        f"{api_count} Steam API DLL(s) found.\n\n"
                        + "\n".join(lines)
                    )
                    messagebox.showinfo("Batch preflight", summary, parent=top)

                def failure(exc, details):
                    update_logs(f"\n[!] Batch preflight failed: {exc}\n{details}")

                run_background(root, worker, success, failure)

            filter_var.trace_add("write", populate)
            tree.bind("<Double-1>", choose)
            populate()

            buttons = ttk.Frame(top)
            buttons.pack(pady=(0, 10))
            ttk.Button(buttons, text="Use selected game", command=choose).grid(row=0, column=0, padx=5)
            ttk.Button(buttons, text="Preflight selected", command=preflight_selected).grid(row=0, column=1, padx=5)
            ttk.Button(buttons, text="Close", command=top.destroy).grid(row=0, column=2, padx=5)
            filter_entry.focus_set()

        def failure(exc, details):
            installedGamesStatus.config(text="Steam library scan failed")
            update_logs(f"\n[!] Installed-game scan failed: {exc}\n{details}")

        def finish():
            installedGamesButton.config(state=tk.NORMAL)

        run_background(root, worker, success, failure, finish)

    def RestoreOriginalFiles():
        if not folder_path or not os.path.isdir(folder_path):
            update_logs("\n[!] Select a valid game folder before restoring files.")
            return

        try:
            manifest = load_manifest(folder_path)
            if manifest:
                entries = manifest["entries"]
                source = "SAC restore manifest"
            else:
                entries = discover_legacy_backups(
                    folder_path,
                    config["FileNames"]["SteamAPI"],
                    config["FileNames"]["SteamAPI64"],
                    config["FileNames"]["GameEXE"],
                )
                source = "legacy backup discovery"
        except Exception as exc:
            update_logs(f"\n[!] Could not inspect restore data: {exc}")
            return

        if not entries:
            update_logs("\nNo restorable SAC backups were found in the selected folder.")
            return

        if not messagebox.askyesno(
            "Restore original files",
            "Restore original files in the selected folder?\n\n"
            "Current modified files will be preserved with a .sac-replaced suffix "
            "instead of being deleted.",
        ):
            return

        selectFolderButton.config(state=tk.DISABLED)
        installedGamesButton.config(state=tk.DISABLED)
        searchGameButton.config(state=tk.DISABLED)
        selectCrackButton.config(state=tk.DISABLED)
        crackGameButton.config(state=tk.DISABLED)
        restoreFilesButton.config(state=tk.DISABLED)
        root.update()

        update_logs(f"\nRestoring original files using {source}...")
        if not manifest:
            update_logs(
                "\n[!] Legacy restore can only identify known backup pairs. "
                "Additional files created by older SAC builds may remain and are not removed automatically."
            )
        try:
            result = restore_entries(folder_path, entries)

            for restored_path in result["restored"]:
                update_logs(f"\n- Restored original: {restored_path}")
            for created_path in result["removed_created"]:
                update_logs(f"\n- Removed SAC-created file from active path: {created_path}")
            for preserved_path in result["preserved"]:
                update_logs(f"\n- Preserved modified file as: {preserved_path}")
            for skipped in result["skipped"]:
                update_logs(
                    "\n[!] Skipped restore entry: "
                    + str(skipped.get("entry"))
                    + " ("
                    + str(skipped.get("reason"))
                    + ")"
                )

            if manifest and not result["skipped"]:
                remove_manifest(folder_path)

            update_logs(
                f"\nRestore finished: {len(result['restored'])} originals restored, "
                f"{len(result['removed_created'])} SAC-created files removed from active paths, "
                f"{len(result['preserved'])} modified files preserved, "
                f"{len(result['skipped'])} skipped."
            )
        except Exception as exc:
            update_logs(f"\n[!] Restore failed: {exc}")
        finally:
            selectFolderButton.config(state=tk.NORMAL)
            installedGamesButton.config(state=tk.NORMAL)
            searchGameButton.config(state=tk.NORMAL)
            selectCrackButton.config(state=tk.NORMAL)
            crackGameButton.config(state=tk.NORMAL)
            restoreFilesButton.config(state=tk.NORMAL, text="Restore original files")
            root.update()


    def update_logs(log_message):
        # Append directly instead of re-reading/deleting/reinserting the entire
        # Text widget for every message. Long cracking runs can emit hundreds of
        # log entries, so the old behavior became progressively more expensive.
        logs_text.config(state=tk.NORMAL)
        logs_text.insert(tk.END, str(log_message))
        logs_text.see(tk.END)
        logs_text.config(state=tk.DISABLED)

    def search_game():
        query = gameNameEntry.get().strip()
        if not query:
            update_logs("\n[!] Please enter a valid Name or AppID")
            return

        searchGameButton.config(state=tk.DISABLED)
        selectFolderButton.config(state=tk.DISABLED)
        installedGamesButton.config(state=tk.DISABLED)
        frameCrack2.pack_forget()

        global gameSearchDone
        gameSearchDone = False
        gameFoundStatus.config(text="Retrieving Steam metadata...")

        try:
            retry_max = max(1, min(int(config["Advanced"]["RetryMax"]), 10))
            retry_delay = max(0.5, min(float(config["Advanced"]["RetryDelay"]), 5.0))
        except Exception:
            retry_max = 5
            retry_delay = 2.0

        def worker():
            client = SteamStoreClient(retry_max=retry_max, retry_delay=retry_delay)
            try:
                resolved_appid = int(query)
                matched_name = None
            except ValueError:
                match = client.search_app(query)
                if not match:
                    raise SteamStoreError(
                        f'No sufficiently close Steam Store match was found for "{query}"'
                    )
                resolved_appid = int(match["appid"])
                matched_name = match["name"]

            metadata = client.game_metadata(resolved_appid)
            if (
                config["Advanced"]["BypassGameVerification"] != "1"
                and metadata.get("type") != "game"
            ):
                raise SteamStoreError(
                    f'AppID {metadata["appid"]} is not reported by Steam as a game'
                )
            metadata["matched_name"] = matched_name
            return metadata

        def success(metadata):
            global appID
            global gameName
            global dlcIDs
            global dlcNames
            global gameSearchDone

            appID = int(metadata["appid"])
            gameName = metadata["name"]
            dlcs = metadata.get("dlcs") or []
            dlcIDs = [int(item["appid"]) for item in dlcs]
            dlcNames = [str(item["name"]) for item in dlcs]

            matched = metadata.get("matched_name")
            if matched:
                update_logs(
                    f'\n- Matched "{query}" to "{matched}" (AppID: {appID})'
                )
            update_logs(
                f'\n- Game found: {gameName} — AppID {appID}; '
                f'{len(dlcIDs)} DLC entries retrieved.'
            )
            gameFoundStatus.config(text=f"All details retrieved for {gameName}!")
            gameSearchDone = True
            frameCrack2.pack()

        def failure(exc, details):
            update_logs(f"\n[!] Steam metadata lookup failed: {exc}")
            gameFoundStatus.config(text="Steam lookup failed")
            if isinstance(exc, SteamStoreError):
                update_logs("\n- Try entering the exact AppID if name matching failed.")

        def finish():
            searchGameButton.config(state=tk.NORMAL)
            selectFolderButton.config(state=tk.NORMAL)
            installedGamesButton.config(state=tk.NORMAL)

        run_background(root, worker, success, failure, finish)

    def CrackGame():
        global appID

        # Prevents the user from searching a game or selecting a folder or re-clicking the crack game button
        selectFolderButton.config(state=tk.DISABLED)
        installedGamesButton.config(state=tk.DISABLED)
        searchGameButton.config(state=tk.DISABLED)
        selectCrackButton.config(state=tk.DISABLED)
        crackGameButton.config(state=tk.DISABLED)
        restoreFilesButton.config(state=tk.DISABLED)

        # Do not risk overwriting the only known-good originals from an earlier run.
        try:
            previous_manifest = load_manifest(folder_path)
            legacy_backups = discover_legacy_backups(
                folder_path,
                config["FileNames"]["SteamAPI"],
                config["FileNames"]["SteamAPI64"],
                config["FileNames"]["GameEXE"],
            )
        except Exception as exc:
            update_logs(f"\n[!] Could not inspect existing backups: {exc}")
            EndCrack()
            return

        if previous_manifest or legacy_backups:
            update_logs(
                "\n[!] Existing SAC restore data/backups were found. "
                "Restore the original files before modifying this folder again."
            )
            gameFoundStatus.config(text="Restore originals before another modification")
            EndCrack()
            return

        update_logs("\nApplying selected file modifications...")
        cracked = False
        steamless_attempted = 0
        steamless_succeeded = 0
        steamless_failed = 0
        api_replacements = 0
        backup_count = 0
        created_count = 0

        if config["Crack"]["SelectedCrack"][:3] == "dlc" and len(dlcIDs) == 0: # If a dlc only crack has been selected, but the game has no DLC
            update_logs("-----\nNo DLC is available, and you selected a DLC only crack. Aborting the cracking process.")
            EndCrack()
            return

        configDir = get_resource_path(os.path.join("sac_emu", config["Crack"]["SelectedCrack"])) # "sac_emu/game_ali213" for example
        try:
            config.read(os.path.join(configDir, "config_override.ini"))
        except Exception:
            pass

        configDir = os.path.join(configDir, "files") # "sac_emu/game_ali213/files" for example

        cached_gbe_files = {}
        if config["Crack"]["SelectedCrack"] == "game_goldberg":
            for gbe_name in ("steam_api.dll", "steam_api64.dll"):
                cached_path = get_cached_gbe_dll(get_tool_cache_dir(), gbe_name)
                if cached_path:
                    cached_gbe_files[gbe_name] = cached_path
            if cached_gbe_files:
                update_logs("\n- Using verified cached GBE_FORK Steam API DLLs for this run.")

        # Check if some custom Steamless options have been set up
        steamlessOptions = ""
        try:
            steamlessOptions = config["Developer"]["SteamlessOptions"] + " "
        except:
            pass

        root.update()

        dllLocations = {}
        for root_dir, dirs, files in os.walk(folder_path):
            apiFile = ""
            files_by_lower = {name.casefold(): name for name in files}

            # Use Steamless if configured
            if (
                config["Preferences"]["CrackOption"] != "2"
                and config["Preferences"]["Steamless"] == "1"
                and crackListSteamless[config["Crack"]["SelectedCrack"]]
            ):
                # Run Steamless on every .exe file. If it's not under DRM or not the wrong file, no problem!
                for fileName in files:
                    if not fileName.casefold().endswith(".exe"):
                        continue
                    steamless_attempted += 1
                    update_logs(f"- Attempting to run Steamless on {fileName}")
                    root.update()
                    #update_logs("\n[[[ Steamless logs ]]]")
                    fileLocation = root_dir + "/" + fileName
                    cached_steamless = get_cached_steamless_executable(get_tool_cache_dir())
                    steamless_path = (
                        cached_steamless
                        or get_resource_path(os.path.join("Steamless_CLI", "Steamless.CLI.exe"))
                    )
                    if os.name != "nt":
                        update_logs("- Steamless is Windows-only; skipping this executable on the current platform.")
                        root.update()
                        continue

                    # Modern verified Steamless releases can process the original path
                    # in-place, so SAC no longer needs to temporarily move the EXE.
                    if cached_steamless:
                        try:
                            result = run_modern_steamless(
                                cached_steamless,
                                fileLocation,
                                steamlessOptions.strip(),
                            )
                        except Exception as exc:
                            update_logs(
                                f"- Modern Steamless could not run on {fileName}: {exc}"
                            )
                            update_logs(
                                "\n  Falling back to the bundled Steamless compatibility build."
                            )
                        else:
                            unpacked_path = result["output_path"]
                            if result["unpacked"]:
                                steamless_succeeded += 1
                                update_logs(
                                    f"- Modern Steamless unpacked {fileName} in place "
                                    f"(exit {result['returncode']})."
                                )

                                if config["FileNames"]["GameEXE"] != "":
                                    exe_backup = fileLocation + config["FileNames"]["GameEXE"]
                                    if os.path.exists(exe_backup):
                                        update_logs(
                                            f"[!] Refusing to overwrite existing executable backup: {exe_backup}. "
                                            "Restore originals first."
                                        )
                                        os.remove(unpacked_path)
                                        steamless_succeeded -= 1
                                        steamless_failed += 1
                                        root.update()
                                        continue
                                    shutil.move(fileLocation, exe_backup)
                                    record_change(folder_path, fileLocation, exe_backup)
                                    backup_count += 1
                                else:
                                    os.remove(fileLocation)

                                shutil.move(unpacked_path, fileLocation)
                                root.update()
                                continue

                            detail = (result["stderr"] or result["stdout"]).strip()
                            update_logs(
                                f"- Modern Steamless did not unpack {fileName} "
                                f"(exit {result['returncode']})."
                            )
                            if detail:
                                update_logs("\n  " + detail.splitlines()[-1])
                            update_logs(
                                "\n  Falling back to the bundled Steamless compatibility build."
                            )

                    # Legacy bundled Steamless path retained as a compatibility fallback.
                    shutil.move(fileLocation, fileName)
                    subprocess.call(
                        f'"{steamless_path}" {steamlessOptions}"{fileName}"',
                        shell=True,
                        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                    )

                    if not os.path.isfile(fileName + ".unpacked.exe"):
                        steamless_failed += 1
                        update_logs("- Steamless did not produce an unpacked executable for " + fileName + ".")
                        shutil.move(fileName, fileLocation)
                        root.update()
                        continue

                    steamless_succeeded += 1
                    update_logs(f"- Steamless produced an unpacked executable for {fileName}")
                    if config["FileNames"]["GameEXE"] != "":
                        exe_backup = fileLocation + config["FileNames"]["GameEXE"]
                        if os.path.exists(exe_backup):
                            update_logs(
                                f"[!] Refusing to overwrite existing executable backup: {exe_backup}. "
                                "Restore originals first."
                            )
                            os.remove(fileName + ".unpacked.exe")
                            shutil.move(fileName, fileLocation)
                            steamless_succeeded -= 1
                            steamless_failed += 1
                            root.update()
                            continue
                        shutil.move(fileName, exe_backup)
                        record_change(folder_path, fileLocation, exe_backup)
                        backup_count += 1
                    else:
                        os.remove(fileName)
                    shutil.move(fileName + ".unpacked.exe", fileLocation)
                    root.update()

            steam_api_name = files_by_lower.get("steam_api.dll")
            if steam_api_name:
                apiFile = os.path.join(root_dir, steam_api_name)
                try:
                    apiFileVersion = GetFileVersion(apiFile)
                except Exception:
                    update_logs(
                        "[!] steam_api.dll: could not retrieve the file version. "
                        "The file may already be modified; aborting to preserve restore safety."
                    )
                    EndCrack()
                    return

                dllLocations.setdefault(root_dir, apiFileVersion)
                update_logs(f"- Found {steam_api_name} in {root_dir}, planning crack application")

            steam_api64_name = files_by_lower.get("steam_api64.dll")
            if steam_api64_name:
                apiFile = os.path.join(root_dir, steam_api64_name)
                try:
                    apiFileVersion = GetFileVersion(apiFile)
                except Exception:
                    update_logs(
                        "[!] steam_api64.dll: could not retrieve the file version. "
                        "The file may already be modified; aborting to preserve restore safety."
                    )
                    EndCrack()
                    return

                dllLocations.setdefault(root_dir, apiFileVersion)
                update_logs(f"- Found {steam_api64_name} in {root_dir}, planning crack application")

            if apiFile != "":
                cracked = True
                root.update()

        if config["Preferences"]["CrackOption"] == "2":
            if not dllLocations:
                update_logs("\n[!] No Steam API DLL locations were found; crack-only package was not created.")
                gameFoundStatus.config(text="No Steam API DLL found")
                EndCrack()
                return

            dlc_with_spaces = "".join(
                f"{dlc_id} = {dlc_name}\n"
                for dlc_id, dlc_name in zip(dlcIDs, dlcNames)
            )
            dlc_without_spaces = "".join(
                f"{dlc_id}={dlc_name}\n"
                for dlc_id, dlc_name in zip(dlcIDs, dlcNames)
            )
            replacements = {
                "SAC_AppID": str(appID),
                "SAC_DLC": dlc_with_spaces,
                "SAC_NoSpaceDLC": dlc_without_spaces,
            }

            try:
                archive_path = build_crack_only_archive(
                    game_root=folder_path,
                    game_name=gameName,
                    appid=appID,
                    template_root=configDir,
                    dll_locations=dllLocations,
                    replacements=replacements,
                    output_dir=get_user_path("crack_only"),
                    source_overrides=cached_gbe_files,
                )
            except Exception as exc:
                update_logs(f"\n[!] Crack-only package generation failed: {exc}")
                gameFoundStatus.config(text="Crack-only package failed")
            else:
                update_logs(
                    "\nCrack-only package created without modifying the selected game:\n"
                    + archive_path
                )
                gameFoundStatus.config(text="Crack-only package created")
            EndCrack()
            return

        for dllCurrentLocation, apiFileVersion in dllLocations.items():
            for root_dir, dirs, files in os.walk(configDir):
                relativeRootDir = root_dir[len(configDir) + 1:]
                dllAbsoluteRelativeLocation = os.path.join(dllCurrentLocation, relativeRootDir)

                # To make it look right, add a "\" at the end of relativeRootDir if it is not empty
                if len(relativeRootDir) > 0:
                    relativeRootDir += "\\"

                # Create all missing directories
                for dir in dirs:
                    if not os.path.isdir(os.path.join(dllAbsoluteRelativeLocation, dir)):
                        os.mkdir(os.path.join(dllAbsoluteRelativeLocation, dir))
                        update_logs("Created new directory " + relativeRootDir + dir)
                        root.update()

                # Create all files
                for fileName in files:
                    root.update()
                    target_path = os.path.join(dllAbsoluteRelativeLocation, fileName)
                    target_existed_before = os.path.isfile(target_path)
                    if target_existed_before: # The file already exists in the game, rename it to .bak
                        newName = fileName + config["FileNames"]["BakSuffix"]
                        if fileName == "steam_api.dll" or fileName == "steam_api64.dll":
                            if config["Preferences"]["CrackOption"] != "0": # Only create config
                                update_logs("Ignoring " + relativeRootDir + fileName + " because of the set crack approach")
                                continue

                            if fileName == "steam_api.dll":
                                newName = config["FileNames"]["SteamAPI"]
                            else:
                                newName = config["FileNames"]["SteamAPI64"]

                        if newName == "": # Don't keep a backup of the steam_api(64).dll file
                            os.remove(os.path.join(dllAbsoluteRelativeLocation, fileName))
                            update_logs("Removed old " + relativeRootDir + fileName + " file because no backup file name is set")
                        elif os.path.isfile(os.path.join(dllAbsoluteRelativeLocation, newName)): # Never overwrite the only known-good backup
                            update_logs(
                                "[!] Existing backup found for "
                                + relativeRootDir + fileName
                                + ". Refusing to overwrite it. Restore original files first."
                            )
                            gameFoundStatus.config(text="Existing backup found — restore originals first")
                            EndCrack()
                            return
                        else:
                            original_path = os.path.join(dllAbsoluteRelativeLocation, fileName)
                            backup_path = os.path.join(dllAbsoluteRelativeLocation, newName)
                            shutil.move(original_path, backup_path)
                            record_change(folder_path, original_path, backup_path)
                            backup_count += 1
                            update_logs("Backed up old file " + relativeRootDir + fileName + " -> " + newName)
                    elif fileName == "steam_api.dll" or fileName == "steam_api64.dll": # No existing file, and this file is the steam_api(64).dll one
                        continue # Ignore this file

                    if not target_existed_before:
                        record_change(folder_path, target_path, None)
                        created_count += 1

                    source_path = os.path.join(root_dir, fileName)
                    if fileName in cached_gbe_files:
                        source_path = cached_gbe_files[fileName]
                    shutil.copyfile(source_path, target_path)

                    if fileName in ("steam_api.dll", "steam_api64.dll"):
                        api_replacements += 1

                    # Check if ends with a specific extension, so we can replace the presets inside
                    if any(fileName.endswith(extension) for extension in EXTS_TO_REPLACE):
                        # Read the file's content
                        with open(os.path.join(dllAbsoluteRelativeLocation, fileName), "r", encoding="utf-8") as file:
                            fileContent = file.read()

                        # Replace the presets if any
                        fileContent = fileContent.replace("SAC_AppID", str(appID))
                        fileContent = fileContent.replace("SAC_APIVersion", apiFileVersion)
                        buffer = ""
                        for i in range(len(dlcIDs)):
                            buffer += str(dlcIDs[i]) + " = " + dlcNames[i] + "\n"
                        fileContent = fileContent.replace("SAC_DLC", buffer)
                        buffer = ""
                        for i in range(len(dlcIDs)):
                            buffer += str(dlcIDs[i]) + "=" + dlcNames[i] + "\n"
                        fileContent = fileContent.replace("SAC_NoSpaceDLC", buffer)

                        # Write the changes
                        with open(os.path.join(dllAbsoluteRelativeLocation, fileName), "w", encoding="utf-8") as file:
                            file.write(fileContent)

                    update_logs("Created new file " + relativeRootDir + fileName)


        update_logs("\n-----\nModification pass finished.")
        update_logs(
            f"Summary — Steamless: {steamless_succeeded}/{steamless_attempted} produced an unpacked EXE; "
            f"Steam API replacements: {api_replacements}; backups preserved: {backup_count}; "
            f"new files tracked: {created_count}."
        )

        result = classify_run_result(
            steam_api_replaced=cracked,
            steamless_enabled=config["Preferences"]["Steamless"] == "1",
            steamless_attempted=steamless_attempted,
            steamless_succeeded=steamless_succeeded,
            steamless_failed=steamless_failed,
        )
        update_logs(result["log"])
        if result["key"] != "no_steam_api":
            update_logs("\nLaunch compatibility has NOT been verified.")
        gameFoundStatus.config(text=result["status"])

        has_restore_manifest = os.path.isfile(manifest_path(folder_path))
        if has_restore_manifest:
            if result["restore_recommended"]:
                restoreFilesButton.config(text="Restore original files (recommended)")
                update_logs(
                    "\nRestore data is available. Restore the original files before trying another crack method."
                )
            else:
                update_logs(
                    "\nRestore data was saved. Restore the original files before another modification pass."
                )

        if result["key"] == "steamless_failed":
            try:
                messagebox.showwarning(
                    "Steamless did not unpack the game",
                    "Steamless could not unpack any executable.\n\n"
                    "The Steam API files were changed, but SteamStub or other launch checks may still be active, "
                    "so Steam may still require a valid license.\n\n"
                    "Use 'Restore original files (recommended)' before trying another method.",
                )
            except Exception:
                pass

        EndCrack()

    def EndCrack():
        # Cracking process done!
        ReloadConfig() # Reload the config to remove the overwritten config from config_override.ini

        # Now let's remove locks
        selectFolderButton.config(state=tk.NORMAL)
        installedGamesButton.config(state=tk.NORMAL)
        searchGameButton.config(state=tk.NORMAL)
        selectCrackButton.config(state=tk.NORMAL)
        crackGameButton.config(state=tk.NORMAL)
        if folder_path and os.path.isdir(folder_path):
            restoreFilesButton.config(state=tk.NORMAL)


    # Theming
    AllThemes: dict[str, dict[str, typing.Any]] = ttkbootstrap.themes.standard.STANDARD_THEMES
    ThemeFilter = ('cosmo', 'darkly', 'cyborg')
    ThemeAliases = ('light', 'dark', 'black')
    ThemesSubset = dict([t for t in AllThemes.items() if t[0] in ThemeFilter])
    def GetThemes() -> dict[str, dict[str, typing.Any]]:
        return ThemesSubset
    
    # Changes appearance according to the theme in the config
    def ApplyStyle() -> None:
        global style
        
        if (config["Preferences"]["ThemeOption"] in tuple(GetThemes().keys())):
            ##print(config["Preferences"]["ThemeOption"])
            style.theme_use(config["Preferences"]["ThemeOption"])
            
            style.configure("TFrame", padding=0)
            style.configure("TLabel", padding=6)
            style.configure("TRadiobutton", padding=6)
            style.configure("TButton", padding=10)
            style.configure("TEntry", padding=6)

    # ----- Settings -----

    def _update_external_tool(button, status_label, tool_name, worker):
        button.config(state=tk.DISABLED)
        status_label.config(text=f"Updating {tool_name}...")

        def success(metadata):
            version = metadata.get("version", "unknown")
            digest = metadata.get("asset_sha256", "")
            short_digest = digest[:12] + "..." if digest else "not supplied"
            status_label.config(text=f"{tool_name} ready: {version}")
            update_logs(
                f"\n- {tool_name} updated to {version}; verified asset SHA-256 {short_digest}"
            )

        def failure(exc, details):
            status_label.config(text=f"{tool_name} update failed")
            update_logs(f"\n[!] {tool_name} update failed: {exc}\n{details}")

        def finish():
            button.config(state=tk.NORMAL)

        run_background(root, worker, success, failure, finish)

    def UpdateGBEFork():
        _update_external_tool(
            gbeUpdateButton,
            externalToolsStatus,
            "GBE_FORK",
            lambda: update_gbe_fork(get_tool_cache_dir()),
        )

    def UpdateSteamless():
        _update_external_tool(
            steamlessUpdateButton,
            externalToolsStatus,
            "Steamless",
            lambda: update_steamless(get_tool_cache_dir()),
        )

    def SettingsButton():
        top = tk.Toplevel(root)
        #top.geometry("750x250")
        top.title(f"SteamAutoCracker GUI v{VERSION} - Settings")
        top.resizable(True, True)
        biggerFont = DEFAULT_FONT.copy()
        biggerFont.config(size=10)
        ttk.Label(top, text= "Settings", font=FONT2).pack(padx=200, pady=(10,10), anchor="center")

        ttk.Button(top, text="Reset to default", padding=0, command=ResetSettingsButton).pack(pady=(0,0), anchor="center")

        # Handle scrolling
        scrollCanvas = tk.Canvas(top, width=600, height=450, highlightthickness=0)
        scrollCanvas.pack(pady=(5, 0), side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollFrame = ttk.Frame(scrollCanvas)
        scrollCanvas.create_window((0,0), window=scrollFrame, anchor="nw")

        # Scrollable settings panel.
        scrollbar = tk.Scrollbar(top, command=scrollCanvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scrollCanvas.config(yscrollcommand=scrollbar.set)

        def on_mousewheel(event):
            scrollCanvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        top.bind("<MouseWheel>", on_mousewheel)

        def configure_canvas(event):
            scrollCanvas.config(scrollregion=scrollCanvas.bbox("all"))

        scrollFrame.bind("<Configure>", configure_canvas)
        # Finished handling scrolling

        # Theme options (ThemeOption)
        ttk.Label(scrollFrame, text="Theme:", font=FONT3, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        settings_frame_theme = ttk.Frame(scrollFrame)
        settings_frame_theme.pack(padx=(15, 0), pady=(0, 0), anchor="w")

        # Radios
        global ThemeOption_var
        ThemeOption_var = tk.StringVar()
        ThemeOption_var.set(config["Preferences"]["ThemeOption"])

        # Display subset of themes that correspond to the
        # typical 'light', 'dark', and 'black' theme options
        themeRow = 0
        for themeIdx, themeKey in enumerate(tuple(GetThemes().keys())):
            ttk.Radiobutton(
                settings_frame_theme, text=f"{themeKey} ({ThemeAliases[themeIdx]})", variable=ThemeOption_var,
                value=themeKey, command=lambda: UpdateConfAndUI("Preferences", "ThemeOption", ThemeOption_var.get())
            ).grid(padx=(4, 4), pady=(2,2), row=themeRow, column=0, sticky="w")
            ##print(f"{themeRow} {themeCol}")
            themeRow += 1
        
        # Update options (UpdateOption)
        ttk.Label(scrollFrame, text="Updates:", font=FONT3, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        ttk.Label(scrollFrame, text="This checks the latest maintained-fork release on GitHub.\nIf you prefer not to make that request automatically, disable automatic update checks.", font=FONT4, padding=0, foreground="#575757", wraplength=600).pack(padx=(6, 0), pady=(0,0), anchor="w")
        settings_frame_updates = ttk.Frame(scrollFrame)
        settings_frame_updates.pack(padx=(15, 0), pady=(0, 0), anchor="w")

        ## Radio
        global UpdateOption_var
        UpdateOption_var = tk.StringVar()
        UpdateOption_var.set(config["Preferences"]["UpdateOption"])
        ttk.Radiobutton(settings_frame_updates, text="Don't automatically check for updates (RECOMMENDED FOR PRIVACY)", variable=UpdateOption_var, value="0", command=lambda: UpdateConfigKey("Preferences", "UpdateOption", UpdateOption_var.get())).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(settings_frame_updates, text="Automatically check for updates on SAC start (RECOMMENDED FOR CONVENIENCE)", variable=UpdateOption_var, value="1", command=lambda: UpdateConfigKey("Preferences", "UpdateOption", UpdateOption_var.get())).grid(row=1, column=0, sticky="w")

        # Crack approach (CrackOption)
        ttk.Label(scrollFrame, text="Crack approach:", font=FONT3, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        settings_frame1 = ttk.Frame(scrollFrame)
        settings_frame1.pack(padx=(15, 0), pady=(0, 0), anchor="w")

        ## Radio
        global CrackOption_var
        CrackOption_var = tk.StringVar()
        CrackOption_var.set(config["Preferences"]["CrackOption"])
        ttk.Radiobutton(settings_frame1, text="Crack the game automatically (RECOMMENDED)", variable=CrackOption_var, value="0", command=lambda: UpdateConfigKey("Preferences", "CrackOption", CrackOption_var.get())).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(settings_frame1, text="Only create the crack config, and put it in the same directory as steam_api(64).dll", variable=CrackOption_var, value="1", command=lambda: UpdateConfigKey("Preferences", "CrackOption", CrackOption_var.get())).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(settings_frame1, text="Build a crack-only ZIP beside SteamAutoCracker (does not modify the selected game)", variable=CrackOption_var, value="2", command=lambda: UpdateConfigKey("Preferences", "CrackOption", CrackOption_var.get())).grid(row=2, column=0, sticky="w")

        # Steamless (Steamless)
        ttk.Label(scrollFrame, text="Steamless:", font=FONT3, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        ttk.Label(scrollFrame, text="This will allow SAC to bypass the SteamStub DRM if it is used.", font=FONT4, padding=0, foreground="#575757", wraplength=600).pack(padx=(6, 0), pady=(0,0), anchor="w")

        settings_frame2 = ttk.Frame(scrollFrame)
        settings_frame2.pack(padx=(15, 0), pady=(0, 10), anchor="w")

        ## Radio
        global Steamless_var
        Steamless_var = tk.StringVar()
        Steamless_var.set(config["Preferences"]["Steamless"])
        ttk.Radiobutton(settings_frame2, text="Don't attempt to use Steamless", variable=Steamless_var, value="0", command=lambda: UpdateConfigKey("Preferences", "Steamless", Steamless_var.get())).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(settings_frame2, text="Attempt to use Steamless (RECOMMENDED)", variable=Steamless_var, value="1", command=lambda: UpdateConfigKey("Preferences", "Steamless", Steamless_var.get())).grid(row=1, column=0, sticky="w")

        ttk.Label(scrollFrame, text="Maintained external tools:", font=FONT3, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        ttk.Label(
            scrollFrame,
            text="Optional verified updates are stored beside SAC, not inside the game. Downloads are checked against GitHub's reported size and SHA-256 digest. Modern Steamless-KR needs .NET 9; SAC falls back to the bundled compatibility build if it cannot run.",
            font=FONT4,
            padding=0,
            foreground="#575757",
            wraplength=600,
        ).pack(padx=(6, 0), pady=(0,0), anchor="w")

        externalToolsFrame = ttk.Frame(scrollFrame)
        externalToolsFrame.pack(padx=(15, 0), pady=(0, 10), anchor="w")

        global gbeUpdateButton
        global steamlessUpdateButton
        global externalToolsStatus

        gbeUpdateButton = ttk.Button(
            externalToolsFrame,
            text="Update GBE_FORK",
            padding=4,
            command=UpdateGBEFork,
        )
        gbeUpdateButton.grid(row=0, column=0, padx=(0, 8))

        steamlessUpdateButton = ttk.Button(
            externalToolsFrame,
            text="Update Steamless",
            padding=4,
            command=UpdateSteamless,
        )
        steamlessUpdateButton.grid(row=0, column=1)

        gbe_meta = get_cached_gbe_metadata(get_tool_cache_dir()) or {}
        steamless_meta = get_cached_steamless_metadata(get_tool_cache_dir()) or {}
        cached_summary = (
            "GBE_FORK: "
            + str(gbe_meta.get("version", "bundled fallback"))
            + " | Steamless: "
            + str(steamless_meta.get("version", "bundled fallback"))
        )
        externalToolsStatus = ttk.Label(externalToolsFrame, text=cached_summary)
        externalToolsStatus.grid(row=1, column=0, columnspan=2, sticky="w")

        # FileNames
        ttk.Label(scrollFrame, text="File names:", font=FONT3, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        ttk.Label(scrollFrame, text="You can enter the name the different files will have.\nIt is recommended to keep the default ones.", font=FONT4, padding=0, foreground="#575757", wraplength=600).pack(padx=(6, 0), pady=(0,0), anchor="w")

        fileNamesFrame = ttk.Frame(scrollFrame)
        fileNamesFrame.pack(padx=(15, 0), pady=(0, 10), anchor="w")

        tk.Label(fileNamesFrame, text="steam_api.dll backup name:").grid(row=0, column=0)
        global SteamApi_var
        SteamApi_var = tk.StringVar()
        steamApiEntry = tk.Entry(fileNamesFrame, width=35, textvariable=SteamApi_var)
        steamApiEntry.grid(row=0, column=1, ipadx=10, ipady=3)
        SteamApi_var.set(config["FileNames"]["SteamAPI"])
        ttk.Button(fileNamesFrame, text="Save", padding=3, command=lambda: UpdateFileName("SteamAPI", SteamApi_var)).grid(row=0, column=2, ipadx=10)

        tk.Label(fileNamesFrame, text="steam_api64.dll backup name:").grid(row=1, column=0)
        global SteamApi64_var
        SteamApi64_var = tk.StringVar()
        steamApiEntry = tk.Entry(fileNamesFrame, width=35, textvariable=SteamApi64_var)
        steamApiEntry.grid(row=1, column=1, ipadx=10, ipady=3)
        SteamApi64_var.set(config["FileNames"]["SteamAPI64"])
        ttk.Button(fileNamesFrame, text="Save", padding=3, command=lambda: UpdateFileName("SteamAPI64", SteamApi64_var)).grid(row=1, column=2, ipadx=10)

        tk.Label(fileNamesFrame, text="Game EXE backup suffix:").grid(row=2, column=0)
        global GameEXE_var
        GameEXE_var = tk.StringVar()
        steamApiEntry = tk.Entry(fileNamesFrame, width=35, textvariable=GameEXE_var)
        steamApiEntry.grid(row=2, column=1, ipadx=10, ipady=3)
        GameEXE_var.set(config["FileNames"]["GameEXE"])
        ttk.Button(fileNamesFrame, text="Save", padding=3, command=lambda: UpdateFileName("GameEXE", GameEXE_var)).grid(row=2, column=2, ipadx=10)

        tk.Label(fileNamesFrame, text="Other files backup suffix:").grid(row=3, column=0)
        global BakSuffix_var
        BakSuffix_var = tk.StringVar()
        steamApiEntry = tk.Entry(fileNamesFrame, width=35, textvariable=BakSuffix_var)
        steamApiEntry.grid(row=3, column=1, ipadx=10, ipady=3)
        BakSuffix_var.set(config["FileNames"]["BakSuffix"])
        ttk.Button(fileNamesFrame, text="Save", padding=3, command=lambda: UpdateFileName("BakSuffix", BakSuffix_var)).grid(row=3, column=2, ipadx=10)

        # Advanced
        ttk.Label(scrollFrame, text="Advanced:", font=FONT3, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        ttk.Label(scrollFrame, text="Advanced settings, don't modify unless you know what you're doing.", font=FONT4, padding=0, foreground="#575757", wraplength=600).pack(padx=(6, 0), pady=(0,0), anchor="w")

        advTextFrame = ttk.Frame(scrollFrame)
        advTextFrame.pack(padx=(15, 0), pady=(0, 10), anchor="w")

        tk.Label(advTextFrame, text="RetryDelay:").grid(row=0, column=0)
        global RetryDelay_var
        RetryDelay_var = tk.StringVar()
        steamApiEntry = tk.Entry(advTextFrame, width=35, textvariable=RetryDelay_var)
        steamApiEntry.grid(row=0, column=1, ipadx=10, ipady=3)
        RetryDelay_var.set(config["Advanced"]["RetryDelay"])
        ttk.Button(advTextFrame, text="Save", padding=3, command=lambda: UpdateAdvanced("RetryDelay", RetryDelay_var)).grid(row=0, column=2, ipadx=10)

        tk.Label(advTextFrame, text="RetryMax:").grid(row=1, column=0)
        global RetryMax_var
        RetryMax_var = tk.StringVar()
        steamApiEntry = tk.Entry(advTextFrame, width=35, textvariable=RetryMax_var)
        steamApiEntry.grid(row=1, column=1, ipadx=10, ipady=3)
        RetryMax_var.set(config["Advanced"]["RetryMax"])
        ttk.Button(advTextFrame, text="Save", padding=3, command=lambda: UpdateAdvanced("RetryMax", RetryMax_var)).grid(row=1, column=2, ipadx=10)

        global BypassGameVerification_var
        BypassGameVerification_var = tk.StringVar()
        BypassGameVerification_var.set(config["Advanced"]["BypassGameVerification"])
        advBypassGameVerification = ttk.Checkbutton(scrollFrame, text="Bypass the game verification, allows to crack AppIDs not recognized as games", variable=BypassGameVerification_var, command=lambda: UpdateAdvanced("BypassGameVerification", BypassGameVerification_var))
        advBypassGameVerification.pack(padx=(15, 0), pady=(0, 10), anchor="w")

        # Place at same pos as root window, with the same size
        # instead of default position (which sometimes is on the other monitor)
        top.geometry(f"{root.winfo_width()}x{root.winfo_height()}+{root.winfo_x()}+{root.winfo_y()}")

        top.grab_set() # Catches all interactions, prevents the user from interacting with the root window

    def UpdateFileName(key, strVar):
        value = strVar.get().strip()
        strVar.set(value)
        UpdateConfigKey("FileNames", key, value)

    def UpdateAdvanced(key, strVar):
        value = strVar.get().strip()
        try:
            int(value)
        except:
            strVar.set(config["Advanced"][key])
        else: # If no error
            strVar.set(value)
            UpdateConfigKey("Advanced", key, value)

    def ResetSettingsButton():
        ResetConfig(1)

        # Update the radio buttons values
        ThemeOption_var.set(config["Preferences"]["ThemeOption"])
        ApplyStyle()
        UpdateOption_var.set(config["Preferences"]["UpdateOption"])
        CrackOption_var.set(config["Preferences"]["CrackOption"])
        Steamless_var.set(config["Preferences"]["Steamless"])
        SteamApi_var.set(config["FileNames"]["SteamAPI"])
        SteamApi64_var.set(config["FileNames"]["SteamAPI64"])
        GameEXE_var.set(config["FileNames"]["GameEXE"])
        BakSuffix_var.set(config["FileNames"]["BakSuffix"])
        RetryDelay_var.set(config["Advanced"]["RetryDelay"])
        RetryMax_var.set(config["Advanced"]["RetryMax"])
        BypassGameVerification_var.set(config["Advanced"]["BypassGameVerification"])

    # ----- Crack List -----

    crackList = { # A list of all selectable cracks
        "game_ali213": ["ALI213 (Game)", "The ALI213 crack is simple and can crack a full game. It will unlock all DLCs and will also prevent the game from connecting to the internet.\nThe game folder can then freely be shared with others as the crack is contained inside the game folder.\nIf it doesn't work, consider using Goldberg instead."],
        "game_goldberg": ["GBE_FORK / Goldberg (Game)", "Uses the bundled Goldberg-compatible template. You can optionally download verified, current GBE_FORK Steam API DLLs from Settings; cached DLLs are preferred automatically.\nInternet connection is blocked, but LAN is enabled."],
        "dlc_creamapi": ["CreamAPI (DLC)", "The CreamAPI crack will unlock all DLCs but will not crack the main game. It is meant to be used with bought copies of a game, with your real Steam account.\nOnly use this is you have purchased the game on Steam and want to unlock its DLCs.\nWill not work for most online games, but might exceptionally work with some like Beat Saber."]
    }

    crackListSteamless = { # Whether to use Steamless with a specific crack. True = use Steamless
        "game_ali213": True,
        "game_goldberg": True,
        "dlc_creamapi": False
    }

    def DisplayCrackList():
        top = tk.Toplevel(root)
        top.title(f"SteamAutoCracker GUI v{VERSION} - Crack List")
        top.resizable(False, False) # Prevents resizing the window's width and height
        biggerFont = DEFAULT_FONT.copy()
        biggerFont.config(size=10)
        ttk.Label(top, text= "Crack List", font=FONT2).pack(padx=200, pady=(10,10), anchor="center")

        ttk.Button(top, text="Reset to default", padding=0, command=ResetCrackListButton).pack(pady=(0,0), anchor="center")

        # Selected crack (SelectedCrack)
        ttk.Label(top, text="Selected crack:", font=FONT3, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        settings_frame1 = ttk.Frame(top)
        settings_frame1.pack(padx=(15, 0), pady=(0, 0), anchor="w")

        ## Radio
        global SelectedCrack_var
        SelectedCrack_var = tk.StringVar()
        SelectedCrack_var.set(config["Crack"]["SelectedCrack"])
        rowNum = 0
        for k, v in crackList.items():
            ttk.Radiobutton(settings_frame1, text=v[0], variable=SelectedCrack_var, value=k, command=lambda: UpdateSelectedCrack()).grid(row=rowNum, column=0, sticky="w")
            rowNum += 1
            if len(v) > 1: # Contains a description
                tk.Label(settings_frame1, text=v[1], font=FONT4, foreground="#575757", wraplength=700, justify="left").grid(row=rowNum, column=0, sticky="w", ipadx=20)
                rowNum += 1

        # Spacer
        tk.Label(top, text="").pack()

        top.grab_set() # Catches all interactions, prevents the user from interacting with the root window

    def UpdateSelectedCrack():
        value = SelectedCrack_var.get()
        UpdateConfigKey("Crack", "SelectedCrack", value)
        UpdateSelectedCrackDisplay()

    def UpdateSelectedCrackDisplay():
        selectCrackButton.config(text=crackList[config["Crack"]["SelectedCrack"]][0]) # Display the name of the selected crack on the select crack button in the root window

    def ResetCrackListButton():
        ResetConfig(2)

        # Update the radio buttons values
        SelectedCrack_var.set(config["Crack"]["SelectedCrack"])

        # Update the root button's text
        UpdateSelectedCrackDisplay()

    # ---------------------------------------

    def UpdateConfig():
        with open(get_user_path("config.ini"), "w", encoding="utf-8") as configFile:
            config.write(configFile)

    def UpdateConfAndUI(section: str, key: str, value: str):
        UpdateConfigKey(section, key, value)
        # Reapply with new selection
        ApplyStyle()

    def UpdateConfigKey(section: str, key: str, value: str):
        config[section][key] = value
        UpdateConfig()

    def ResetConfig(resetLevel = 0, customConfig=None):
        """resetLevel values:
        0 = Everything
        1 = Main settings only (Preferences, FileNames, Advanced)
        2 = Crack selection settings only (Crack)
        """
        if customConfig:
            currentConfig = customConfig
        else:
            currentConfig = config

        if resetLevel == 0 or resetLevel == 1:
            currentConfig["Preferences"] = {}
            currentConfig["Preferences"]["ThemeOption"] = list(GetThemes().keys())[0]
            currentConfig["Preferences"]["UpdateOption"] = "0"
            currentConfig["Preferences"]["CrackOption"] = "0"
            currentConfig["Preferences"]["Steamless"] = "1"
            currentConfig["Preferences"]["last_selected_folder"] = ""

            currentConfig["FileNames"] = {}
            currentConfig["FileNames"]["GameEXE"] = ".bak"
            currentConfig["FileNames"]["BakSuffix"] = ".bak"
            currentConfig["FileNames"]["SteamAPI"] = "steam_api.dll.bak"
            currentConfig["FileNames"]["SteamAPI64"] = "steam_api64.dll.bak"

            currentConfig["Advanced"] = {}
            currentConfig["Advanced"]["RetryDelay"] = str(RETRY_DELAY)
            currentConfig["Advanced"]["RetryMax"] = str(RETRY_MAX)
            currentConfig["Advanced"]["BypassGameVerification"] = "0"
        if resetLevel == 0 or resetLevel == 2:
            currentConfig["Crack"] = {}
            currentConfig["Crack"]["SelectedCrack"] = "game_ali213"

        if not customConfig:
            UpdateConfig()

    def FillConfig(currentConfig, configDefault):
        changed = False
        for k, v in configDefault.items():
            if k not in currentConfig:
                currentConfig[k] = v
                print("Updated", k, "->", v)
                changed = True
            if type(v) == configparser.SectionProxy:
                if FillConfig(currentConfig[k], v):
                    changed = True

        return changed

    def ReloadConfig():
        global config
        config = configparser.ConfigParser()

        if config.read(get_user_path("config.ini")) == []:
            # Config doesn't exist, create it
            ResetConfig()
        else:
            # Create a config with default values
            configDefault = configparser.ConfigParser()
            ResetConfig(0, configDefault)

            # Check if the config is complete. If not, complete it.
            changed = FillConfig(config, configDefault)
            if changed:
                print("[SAC] config.ini has been updated, missing entries have been created")
                UpdateConfig()

    ReloadConfig()

    # ---------------------------------------

    def CheckUpdates():
        updatesButton.config(text="Searching for fork updates...", state=tk.DISABLED)
        root.update()

        try:
            req = SACRequest(FORK_LATESTRELEASEJSON, "RetrieveForkLatestRelease").req
            data = req.json()
            latest = str(data["tag_name"]).lstrip("vV")
        except Exception as exc:
            updatesButton.config(text="Update check failed", state=tk.NORMAL)
            update_logs(f"\n[!] Fork update check failed: {exc}")
            return

        global latestversion
        global release_link
        latestversion = latest
        release_link = data.get(
            "html_url",
            f"https://github.com/{FORK_REPO}/releases/latest",
        )

        if version_key(latestversion) <= version_key(VERSION):
            updatesButton.config(text="SAC fork is up to date!", state=tk.NORMAL)
            return

        updatesButton.config(text="New fork release available", state=tk.NORMAL)
        DisplayUpdate()

    def DisplayUpdate():
        top = tk.Toplevel(root)
        top.title(f"SteamAutoCracker GUI v{VERSION} - Update")
        top.resizable(False, False) # Prevents resizing the window's width and height
        biggerFont = DEFAULT_FONT.copy()
        biggerFont.config(size=10)
        ttk.Label(top, text= "Update", font=FONT2).pack(padx=200, pady=(10,10), anchor="center")
        ttk.Label(top, text="A newer wefalltomorrow SteamAutoCracker release is available.\nOpen the release page to review and download it.", font=biggerFont, padding=0).pack(padx=(6, 0), pady=(10,0), anchor="w")
        ttk.Label(top, text=f"Current version: {VERSION}", font=biggerFont, padding=0).pack(padx=(6, 0), pady=(15,0), anchor="w")
        ttk.Label(top, text=f"Latest version: {latestversion}", font=biggerFont, padding=0).pack(padx=(6, 0), pady=(0,10), anchor="w")

        updateDisplayButtonsFrame = ttk.Frame(top)
        updateDisplayButtonsFrame.pack(pady=(5,20))

        global updateDisplayButtonUpdate
        updateDisplayButtonUpdate = ttk.Button(updateDisplayButtonsFrame, text="Open fork release", command=UpdateSAC, padding=3)
        updateDisplayButtonUpdate.grid(row=0, column=0)

        global updateDisplayButtonCopy
        updateDisplayButtonCopy = ttk.Button(updateDisplayButtonsFrame, text="Copy the release URL", command=CopyReleaseURL, padding=3)
        updateDisplayButtonCopy.grid(row=0, column=1, padx=(50,0))

        global updateDisplayButtonClose
        updateDisplayButtonClose = ttk.Button(updateDisplayButtonsFrame, text="Don't update yet", command=top.destroy, padding=3)
        updateDisplayButtonClose.grid(row=0, column=2, padx=(50,0))

        global updateDisplayStatusLabel
        updateDisplayStatusLabel = ttk.Label(top, text="", font=biggerFont, padding=0)

        top.grab_set() # Catches all interactions, prevents the user from interacting with the root window

        global updateDisplayTop
        updateDisplayTop = top

    def UpdateSAC():
        updateDisplayStatusLabel.pack(pady=(0,20), anchor="center")
        updateDisplayStatusLabel.config(
            text="Opening the maintained fork release page in your browser.\n"
                 "Downloads are manual so you can review the release before replacing your current build."
        )
        root.update()
        webbrowser.open(release_link)

    def CopyReleaseURL():
        root.clipboard_clear()
        root.clipboard_append(release_link)

    # ---------------------------------------


    # Let's now create the main window
    root = TkinterDnD.Tk()
    root.resizable(True, True) # Allow the window to be resized.
    root.minsize(800, 600)
    root.title(f"SteamAutoCracker GUI v{VERSION}")
    root.drop_target_register(DND_FILES) # Register the drop target
    root.dnd_bind("<<Drop>>", lambda event: handle_folder_selection(event=event)) # Bind the drop target

    DEFAULT_FONT = font.nametofont('TkTextFont')
    FONT2 = DEFAULT_FONT.copy()
    FONT2.config(size=15)
    FONT3 = DEFAULT_FONT.copy()
    FONT3.config(size=12)
    FONT4 = DEFAULT_FONT.copy()
    FONT4.config(size=8)
    FONT_APP_ENTRY = DEFAULT_FONT.copy()
    FONT_APP_ENTRY.config(size=10)

    # Style ttk
    style: ttkbootstrap.Style = ttkbootstrap.Style(theme=config["Preferences"]["ThemeOption"])
    
    ApplyStyle()

    ttk.Label(root, text=f"SteamAutoCracker GUI v{VERSION}", font=FONT2, padding=0).pack(pady=(10, 0), anchor="center")
    ttk.Label(root, text="BigBoiCJ base · maintained by wefalltomorrow", padding=0).pack(pady=(0, 0), anchor="center")

    updatesFrame = tk.Frame(root)
    updatesButton = ttk.Button(updatesFrame, text="Check for updates", command=CheckUpdates, padding=0)
    updatesButton.grid(row=0, column=0)
    updatesFrame.pack(pady=(0, 20))

    ttk.Button(root, text="Settings", command=SettingsButton, padding=8).pack(pady=(0, 20), anchor="center")

    """
    frame4 = ttk.Frame(root)
    frame4.pack(pady=(5, 0), padx=10, anchor="center")"""

    ttk.Separator(root, orient='horizontal').pack(fill="x", padx=220)

    # Select folder fields
    tk.Label(root, text="Select where your game is installed :",).pack(pady=(20, 5), anchor="center")
    folderButtonsFrame = ttk.Frame(root)
    folderButtonsFrame.pack(pady=(0, 4))

    selectFolderButton = ttk.Button(
        folderButtonsFrame,
        text="Select a folder",
        command=lambda: handle_folder_selection(),
    )
    selectFolderButton.grid(row=0, column=0, padx=(0, 6))

    installedGamesButton = ttk.Button(
        folderButtonsFrame,
        text="Installed Steam games",
        command=BrowseInstalledGames,
    )
    installedGamesButton.grid(row=0, column=1, padx=(6, 0))

    installedGamesStatus = ttk.Label(root, text="")
    installedGamesStatus.pack(pady=(0, 8))

    selectedFolderFrame = tk.Frame(root) # This frame will contain the label. This is so we can resize the root window properly when the text is empty.
    selectedFolderFrame.pack()
    tk.Frame(selectedFolderFrame, width=1, height=1).pack() # 1x1 frame, else selectedFolderFrame will not update its size after it is emptied (by selectedFolderLabel.pack_forget)
    selectedFolderLabel = tk.Label(selectedFolderFrame, text="", wraplength=700)
    selectedFolderLabel.pack()
    selectedFolderLabel.pack_forget()

    restoreFilesButton = ttk.Button(
        root,
        text="Restore original files",
        padding=5,
        command=RestoreOriginalFiles,
    )
    restoreFilesButton.pack_forget()

    # Enter game name or appID fields
    frameGame = ttk.Frame(root) # Main frame for the game
    frameGame.pack(pady=(5, 0), anchor="center")

    tk.Frame(frameGame, width=1, height=1).pack() # 1x1 frame, else frameGame will not update its size after it is emptied (by frameGame2.pack_forget)
    frameGame2 = ttk.Frame(frameGame) # The elements will be inside this one. This is so we can call pack_forget and still preserve the location of frameGame.
    frameGame2.pack()
    ttk.Separator(frameGame2, orient='horizontal').pack(fill="x", padx=50, pady=(15, 0))
    ttk.Label(frameGame2, text="Enter the Name or AppID of the game you want to Crack:").pack(pady=(15, 0), anchor="center")

    frame4 = ttk.Frame(frameGame2)
    frame4.pack(pady=(5, 0), anchor="center")
    gameNameEntry = tk.Entry(frame4, width=35, font=FONT_APP_ENTRY)
    gameNameEntry.grid(row=0, column=0, ipady=5)
    searchGameButton = ttk.Button(frame4, text="Search", padding=5, command=search_game)
    searchGameButton.grid(row=0, column=1, padx=(10, 0))

    gameFoundStatus = ttk.Label(frameGame2, text="")
    gameFoundStatus.pack(pady=(5, 0), anchor="center")

    frameGame2.pack_forget() # Hide the elements, but preserves their location thanks to frameGame still being packed but empty

    # Crack fields
    frameCrack = ttk.Frame(root)
    frameCrack.pack(pady=(15, 0), anchor="center")
    tk.Frame(frameCrack, width=1, height=1).pack() # 1x1 frame
    frameCrack2 = ttk.Frame(frameCrack)
    frameCrack2.pack()
    ttk.Separator(frameCrack2, orient='horizontal').pack(fill="x", padx=0, pady=(0, 15))
    selectedCrackFrame = ttk.Frame(frameCrack2)
    selectedCrackFrame.pack()
    tk.Label(selectedCrackFrame, text="Selected crack:").grid(row=0, column=0)
    selectCrackButton = ttk.Button(selectedCrackFrame, text="None", padding=5, command=DisplayCrackList)
    selectCrackButton.grid(row=0, column=1, padx=(10, 0))
    UpdateSelectedCrackDisplay() # Updates the text of selectCrackButton
    crackGameButton = ttk.Button(frameCrack2, text="Crack the game", padding=8, command=CrackGame)
    crackGameButton.pack(pady=(10, 0))

    frameCrack2.pack_forget() # Hide the elements, but preserves their location thanks to frameCrack still being packed but empty

    # Spacer
    #tk.Label(root, text="").pack()

    # Logs text widget with a vertical scrollbar; keep a monospaced font.
    logs_frame = ttk.Frame(root)
    logs_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

    logs_scrollbar = ttk.Scrollbar(logs_frame)
    logs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    logs_text = tk.Text(
        logs_frame,
        height=12,
        width=90,
        font="TkFixedFont",
        yscrollcommand=logs_scrollbar.set,
    )
    logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    logs_scrollbar.config(command=logs_text.yview)

    text = f"SteamAutoCracker GUI v{VERSION} by BigBoiCJ"
    buf = ""
    for i in range(len(text)):
        buf += "-"

    logs_text.insert("1.0", f"{buf}\n{text}\n{buf}")
    logs_text.config(state=tk.DISABLED) # Prevents users from editing the text inside logs_text

    # Handle errors to log them while tkinter is running
    root.report_callback_exception = OnTkinterError

    # Check for updates
    if config["Preferences"]["UpdateOption"] == "1":
        CheckUpdates()

    ##root.geometry("636x555")

    # Start main loop
    root.mainloop()

except Exception:
    # Handle Python errors. Keep this independent of helpers defined inside the try block,
    # because an import failure can happen before those helpers exist.
    print("\n[!!!] A Python error occurred! Writing the error to the error.log file.\n---")
    error_base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(error_base, "error.log"), "w", encoding="utf-8") as errorFile:
        errorFile.write(f"SteamAutoCracker GUI v{VERSION}\n---\nA Python error occurred!\nPlease report it on GitHub or cs.rin.ru\nMake sure to blank any personal detail.\n---\n\n")
        traceback.print_exc(file=errorFile)
    traceback.print_exc()
    print("---\nError written to error.log, please report it on GitHub or cs.rin.ru\nMake sure to blank any personal detail.")
