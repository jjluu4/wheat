# wheat/core/github_to_entries.py

from __future__ import annotations
from typing import Any, Dict, Optional
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Entry

def event_to_entry_data(event: Dict[str, Any], author) -> Optional[Dict[str, Any]]:
    """
    Convert a GitHub public event into a dict of Entry fields.
    Returns None if we don't want to create an entry for this event type.
    """
    event_type = event.get("type")
    created_at = event.get("created_at")  # ISO string

    # Basic dedupe ID: GitHub event id is unique globally
    gh_event_id = event.get("id")
    if not gh_event_id:
        return None

    # Build a stable URL for THIS entry in our system
    # (Doesn't need to be perfect yet; just needs to be unique)
    entry_url = f"{author.host}authors/{author.id}/entries/github-{gh_event_id}"

    # Make simple human-readable content
    actor_login = (event.get("actor") or {}).get("login", "someone")
    repo_name = (event.get("repo") or {}).get("name", "a repo")

    if event_type == "PushEvent":
        payload = event.get("payload") or {}
        commits = payload.get("commits") or []
        commit_count = len(commits)
        content = f"{actor_login} pushed {commit_count} commit(s) to {repo_name} on GitHub."
    elif event_type == "CreateEvent":
        payload = event.get("payload") or {}
        ref_type = payload.get("ref_type", "something")
        ref = payload.get("ref")
        ref_part = f" {ref}" if ref else ""
        content = f"{actor_login} created {ref_type}{ref_part} in {repo_name}."
    else:
        # For now, ignore other types (we can add more later)
        return None

    return {
        "url": entry_url,
        "author": author,
        "content": content,
        "content_type": "text/plain",
        "visibility": "PUBLIC",
        # We'll parse created_at to datetime later when we actually save
        "published": created_at,
        # Store raw event id in content for now (we'll add a proper field later if needed)
    }


def save_event_as_entry(event, author):
    data = event_to_entry_data(event, author)
    if not data:
        return None

    # Convert GitHub ISO timestamp -> Django datetime
    published = data.get("published")
    if isinstance(published, str):
        dt = parse_datetime(published)  # e.g. "2026-03-01T08:12:34Z"
        if dt is None:
            dt = timezone.now()
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        data["published"] = dt

    defaults = {
        "author": author,
        "content": data["content"],
        "content_type": data.get("content_type", "text/plain"),
        "visibility": data.get("visibility", "PUBLIC"),
        "published": data["published"],
    }

    entry, _created = Entry.objects.update_or_create(
        url=data["url"],
        defaults=defaults,
    )
    return entry