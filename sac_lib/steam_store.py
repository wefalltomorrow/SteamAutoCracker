def extract_appdetails_entry(payload, appid):
    """Return one AppDetails entry without ever indexing a missing AppID key."""
    app_id = str(appid)

    if not isinstance(payload, dict):
        return None

    entry = payload.get(app_id)
    if isinstance(entry, dict):
        return entry

    # Tolerate a future/single-entry response shape if Steam removes the outer
    # dynamic AppID key.
    if "success" in payload and (
        "data" in payload or payload.get("success") is False
    ):
        return payload

    return None


def describe_appdetails_problem(payload, appid):
    """Produce a short diagnostic for unexpected AppDetails response shapes."""
    app_id = str(appid)

    if isinstance(payload, dict):
        keys = list(payload.keys())
        if not keys:
            return "empty JSON object"
        return (
            f"requested AppID {app_id} key missing; returned keys: "
            + ", ".join(str(key) for key in keys[:5])
        )

    return f"unexpected JSON type: {type(payload).__name__}"
