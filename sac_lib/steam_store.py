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

import re
import time
from difflib import SequenceMatcher

import requests


DEFAULT_HEADERS = {
    "User-Agent": "SteamAutoCracker-wefalltomorrow",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _normalize_name(value):
    value = str(value or "").casefold()
    return " ".join("".join(ch if ch.isalnum() else " " for ch in value).split())


def _name_score(target, candidate):
    target_norm = _normalize_name(target)
    candidate_norm = _normalize_name(candidate)
    if not target_norm or not candidate_norm:
        return 0.0
    if target_norm == candidate_norm:
        return 1.0

    score = SequenceMatcher(None, target_norm, candidate_norm).ratio()
    if target_norm in candidate_norm or candidate_norm in target_norm:
        score = max(score, 0.80)
    return score


class SteamStoreError(RuntimeError):
    pass


class SteamStoreClient:
    """Network-only Steam Store client safe to run outside the Tk UI thread."""

    def __init__(self, retry_max=5, retry_delay=2.0, headers=None):
        self.retry_max = max(1, int(retry_max))
        self.retry_delay = max(0.0, float(retry_delay))
        self.session = requests.Session()
        self.session.headers.update(headers or DEFAULT_HEADERS)

    def _request_json(self, url, params=None, timeout=15):
        last_error = None
        for attempt in range(1, self.retry_max + 1):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt >= self.retry_max:
                    break
                time.sleep(min(self.retry_delay * attempt, 15.0))
        raise SteamStoreError(f"Steam request failed after {self.retry_max} attempts") from last_error

    def search_app(self, term):
        payload = self._request_json(
            "https://store.steampowered.com/api/storesearch/",
            params={"term": term, "cc": "US", "l": "english"},
        )
        items = payload.get("items", []) if isinstance(payload, dict) else []
        candidates = [
            item for item in items
            if isinstance(item, dict) and item.get("id") is not None and item.get("name")
        ]
        if not candidates:
            return None

        best = max(candidates, key=lambda item: _name_score(term, item["name"]))
        if _name_score(term, best["name"]) < 0.45:
            return None
        return {"appid": int(best["id"]), "name": str(best["name"])}

    def app_details(self, appid):
        app_id = str(int(appid))
        variants = [
            {"appids": app_id, "l": "english", "cc": "US"},
            {"appids": app_id, "filters": "basic", "l": "english", "cc": "US"},
        ]
        problems = []

        for params in variants:
            payload = self._request_json(
                "https://store.steampowered.com/api/appdetails",
                params=params,
            )
            entry = extract_appdetails_entry(payload, app_id)
            if entry is not None:
                return entry
            problems.append(describe_appdetails_problem(payload, app_id))

        raise SteamStoreError(
            f"Steam AppDetails did not return AppID {app_id}: " + "; ".join(problems)
        )

    def app_name(self, appid):
        entry = self.app_details(appid)
        if not entry.get("success"):
            return None
        data = entry.get("data")
        if not isinstance(data, dict):
            return None
        return data.get("name")

    def _dlc_ids_from_filtered_page(self, appid):
        try:
            payload = self._request_json(
                f"https://store.steampowered.com/dlc/{int(appid)}/random/ajaxgetfilteredrecommendations/",
                params={"query": "", "count": 10000},
            )
        except SteamStoreError:
            return []

        if not isinstance(payload, dict) or not payload.get("success"):
            return []

        html = str(payload.get("results_html") or "")
        ids = []
        seen = set()
        for match in re.finditer(r'data-ds-appid="(\d+)"', html):
            value = int(match.group(1))
            if value in seen:
                continue
            seen.add(value)
            ids.append(value)
        return ids

    def game_metadata(self, appid):
        app_id = int(appid)
        entry = self.app_details(app_id)
        if not entry.get("success"):
            raise SteamStoreError(f"AppID {app_id} was not found")

        data = entry.get("data")
        if not isinstance(data, dict):
            raise SteamStoreError(f"Steam returned incomplete data for AppID {app_id}")

        game_name = data.get("name")
        if not game_name:
            raise SteamStoreError(f"Steam returned AppID {app_id} without a name")

        dlc_ids = []
        for value in data.get("dlc") or []:
            try:
                value = int(value)
            except (TypeError, ValueError):
                continue
            if value not in dlc_ids:
                dlc_ids.append(value)

        filtered = self._dlc_ids_from_filtered_page(app_id)
        for value in filtered:
            if value not in dlc_ids:
                dlc_ids.append(value)

        dlcs = []
        for dlc_id in dlc_ids:
            try:
                name = self.app_name(dlc_id)
            except SteamStoreError:
                name = None
            dlcs.append({
                "appid": dlc_id,
                "name": name or f"AppID {dlc_id}",
            })

        return {
            "appid": int(data.get("steam_appid", app_id)),
            "name": str(game_name),
            "type": data.get("type"),
            "dlcs": dlcs,
        }

