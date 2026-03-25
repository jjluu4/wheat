import urllib

import requests
import logging

from .auth import add_auth_headers
from .helpers import normalize_url
from .models import Author, Entry, Follow, RemoteNode

logger = logging.getLogger(__name__)


def _extract_author_id_from_fqid(author_fqid):
    path_parts = [part for part in urllib.parse.urlparse(author_fqid).path.split("/") if part]
    for idx, part in enumerate(path_parts):
        if part == "authors" and idx + 1 < len(path_parts):
            return path_parts[idx + 1]
    return None


def _remote_node_for_author(author):
    host = normalize_url(getattr(author, "host", ""))
    if not host or "testserver" in host:
        return None
    base_url = host[:-4] if host.endswith("/api") else host
    return RemoteNode.objects.filter(base_url=base_url, is_active=True).first()


def remote_authors_for_entry(author, visibility):
    followers = Author.objects.filter(
        following__target=author,
        following__status="ACCEPTED",
    ).exclude(host__contains="testserver")

    if visibility in ("PUBLIC", "UNLISTED"):
        return list(followers)

    if visibility != "FRIENDS":
        return []

    friends = Author.objects.filter(
        following__target=author,
        following__status="ACCEPTED",
        followers__actor=author,
        followers__status="ACCEPTED",
    ).exclude(host__contains="testserver")
    return list(friends)


def send_to_author_inbox(target_author, payload, method="POST"):
    remote = _remote_node_for_author(target_author)
    if remote is None:
        return False, "Remote node credentials not configured for target author"

    remote_author_id = _extract_author_id_from_fqid(getattr(target_author, "url", ""))
    if not remote_author_id:
        return False, "Invalid target author URL: unable to parse author id"

    target_host = normalize_url(getattr(target_author, "host", ""))
    inbox_url = f"{target_host}/authors/{remote_author_id}/inbox"
    headers = add_auth_headers({"Content-Type": "application/json"}, remote)

    request_fn = {
        "POST": requests.post,
        "PUT": requests.put,
        "DELETE": requests.delete,
    }.get(method.upper())
    if request_fn is None:
        return False, f"Unsupported method {method}"

    try:
        response = request_fn(inbox_url, json=payload, headers=headers, timeout=10)
    except requests.RequestException as exc:
        return False, str(exc)

    if response.status_code not in (200, 201, 202, 204):
        return False, f"Remote inbox returned status {response.status_code}"
    return True, None


def distribute_entry_to_remote_recipients(author, payload, visibility, method="POST"):
    recipients = remote_authors_for_entry(author, visibility)
    failures = []
    for recipient in recipients:
        ok, error = send_to_author_inbox(recipient, payload, method=method)
        if not ok:
            failures.append({"target": recipient.url, "error": error})
            logger.warning(
                "Entry distribution delivery failed author=%s target=%s method=%s visibility=%s error=%s",
                getattr(author, "url", author.serial),
                getattr(recipient, "url", recipient.serial),
                method,
                visibility,
                error,
            )
    return failures


def _upsert_remote_author(author_payload):
    author_fqid = normalize_url(author_payload.get("id") or author_payload.get("url") or "")
    if not author_fqid:
        return None

    author = Author.objects.filter(url__in=[author_fqid, f"{author_fqid}/"]).first()
    if author is None:
        author = Author(url=author_fqid)

    author.host = normalize_url(author_payload.get("host") or author.host or "")
    author.displayName = author_payload.get("displayName") or author.displayName or "Remote Author"
    author.github = author_payload.get("github") or ""
    author.profileImage = author_payload.get("profileImage") or ""
    author.web = author_payload.get("web") or author.web or author_fqid
    author.save()
    return author


def _fetch_remote_json(url, node):
    headers = add_auth_headers({"Accept": "application/json"}, node)
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def sync_remote_authors_and_public_entries():
    discovered_authors = 0
    discovered_entries = 0

    for node in RemoteNode.objects.filter(is_active=True):
        api_base = normalize_url(node.api_base_url or f"{node.base_url}/api")
        authors_payload = _fetch_remote_json(f"{api_base}/authors", node)
        if not isinstance(authors_payload, dict):
            continue
        authors = authors_payload.get("authors") or []
        if not isinstance(authors, list):
            continue

        for author_payload in authors:
            if not isinstance(author_payload, dict):
                continue
            author = _upsert_remote_author(author_payload)
            if author is None:
                continue
            discovered_authors += 1

            author_id = _extract_author_id_from_fqid(author.url)
            if not author_id:
                continue
            entries_payload = _fetch_remote_json(f"{api_base}/authors/{author_id}/entries/", node)
            if not isinstance(entries_payload, dict):
                continue
            remote_entries = entries_payload.get("entries") or entries_payload.get("src") or []
            if not isinstance(remote_entries, list):
                continue

            for entry_payload in remote_entries:
                if not isinstance(entry_payload, dict):
                    continue
                if entry_payload.get("visibility") not in ("PUBLIC", "UNLISTED", "FRIENDS"):
                    continue
                entry_url = normalize_url(entry_payload.get("id") or entry_payload.get("url") or "")
                if not entry_url:
                    continue
                entry = Entry.objects.filter(url__in=[entry_url, f"{entry_url}/"]).first()
                if entry is None:
                    entry = Entry(url=entry_url, author=author)
                entry.author = author
                entry.title = (entry_payload.get("title") or "").strip() or "Untitled"
                entry.content = entry_payload.get("content") or ""
                entry.content_type = entry_payload.get("contentType") or entry_payload.get("content_type") or "text/plain"
                entry.image_url = entry_payload.get("imageUrl") or entry_payload.get("image_url") or ""
                entry.visibility = entry_payload.get("visibility") if entry_payload.get("visibility") in ("PUBLIC", "UNLISTED", "FRIENDS", "DELETED") else "PUBLIC"
                entry.web = entry_payload.get("web") or entry.web or ""
                entry.save()
                discovered_entries += 1

    return {"authors": discovered_authors, "entries": discovered_entries}

