# core/github.py
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def normalize_github_username(value: str | None) -> str | None:
    """
    Accepts any of these and returns just the username (e.g. "torvalds"):
      - "torvalds"
      - "@torvalds"
      - "https://github.com/torvalds"
      - "https://github.com/torvalds/linux"
      - "github.com/torvalds"
      - "www.github.com/torvalds"
    """
    if not value:
        return None

    value = value.strip()

    # handle "@username"
    if value.startswith("@"):
        value = value[1:].strip()

    # handle "github.com/username" (no scheme)
    if value.startswith("github.com/") or value.startswith("www.github.com/"):
        value = "https://" + value

    # URL case
    if value.startswith("http://") or value.startswith("https://"):
        p = urlparse(value)
        path = (p.path or "").strip("/")  # "torvalds" or "torvalds/linux"
        if not path:
            return None
        return path.split("/")[0]

    # plain string case (might still include extra path)
    value = value.strip("/")
    if not value:
        return None
    return value.split("/")[0]


def fetch_public_events(github_url: str, *, per_page: int = 10) -> list[dict]:
    username = normalize_github_username(github_url)
    if not username:
        return []

    # GitHub API: per_page max is 100
    try:
        per_page = max(1, min(int(per_page), 100))
    except (TypeError, ValueError):
        per_page = 10

    api_url = f"https://api.github.com/users/{username}/events/public?per_page={per_page}"
    req = Request(
        api_url,
        headers={
            "User-Agent": "wheat-cmput404",
            "Accept": "application/vnd.github+json",
        },
    )

    try:
        with urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []