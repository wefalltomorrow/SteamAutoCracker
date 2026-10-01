def classify_run_result(
    *,
    steam_api_replaced,
    steamless_enabled,
    steamless_attempted,
    steamless_succeeded,
    steamless_failed,
):
    """Return the GUI status and log text for a completed modification pass."""

    if not steam_api_replaced:
        return {
            "key": "no_steam_api",
            "status": "No Steam API DLL found",
            "log": "[!] No Steam API DLL was found in the selected folder.",
            "restore_recommended": False,
        }

    if (
        steamless_enabled
        and steamless_attempted > 0
        and steamless_succeeded == 0
    ):
        return {
            "key": "steamless_failed",
            "status": "Steamless failed — DRM removal incomplete",
            "log": (
                "[!] Steamless did not unpack any executable. The Steam API files were "
                "modified, but SteamStub/launch checks may still be active and Steam may "
                "still require a valid license. Restore the original files before trying "
                "another approach."
            ),
            "restore_recommended": True,
        }

    if steamless_failed > 0:
        return {
            "key": "partial",
            "status": "Completed with warnings — launch not verified",
            "log": (
                "[!] Some executables were not processed by Steamless. Files were modified, "
                "but launch compatibility has not been verified."
            ),
            "restore_recommended": True,
        }

    return {
        "key": "modified",
        "status": "Files modified — launch not verified",
        "log": "File modifications completed. Launch compatibility has not been verified.",
        "restore_recommended": False,
    }
