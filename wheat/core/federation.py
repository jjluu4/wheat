import logging
from .helpers import (
    fetch_remote_json,
    normalize_url,
    parse_author_fqid,
    send_json_to_remote_author_inbox,
    upsert_remote_author,
)
from .models import Author, Entry, RemoteNode

logger = logging.getLogger(__name__)

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
    return send_json_to_remote_author_inbox(getattr(target_author, "url", ""), payload, method=method)


def distribute_payload_to_remote_recipients(author, payload, visibility, method="POST"):
    """
    Deliver arbitrary JSON to remote inboxes for the set of recipients allowed
    by `visibility` (PUBLIC/UNLISTED -> followers, FRIENDS -> mutuals/friends).
    """
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


def distribute_entry_to_remote_recipients(author, payload, visibility, method="POST"):
    # Backwards-compatible wrapper (other modules import this symbol).
    return distribute_payload_to_remote_recipients(
        author=author,
        payload=payload,
        visibility=visibility,
        method=method,
    )


def create_or_update_entry_from_remote_payload(entry_payload, author):
    entry_url = normalize_url(entry_payload.get("id") or entry_payload.get("url") or "")
    if not entry_url:
        return None

    entry = Entry.objects.filter(url__in=[entry_url, f"{entry_url}/"]).first()
    if entry is None:
        entry = Entry(url=entry_url, author=author)

    entry.author = author
    entry.title = (entry_payload.get("title") or "").strip() or "Untitled"
    entry.content = entry_payload.get("content") or ""
    entry.content_type = (
        entry_payload.get("contentType") or entry_payload.get("content_type") or "text/plain"
    )
    entry.image_url = entry_payload.get("imageUrl") or entry_payload.get("image_url") or ""

    visibility = entry_payload.get("visibility")
    entry.visibility = (
        visibility if visibility in ("PUBLIC", "UNLISTED", "FRIENDS", "DELETED") else "PUBLIC"
    )

    entry.web = entry_payload.get("web") or entry.web or ""
    entry.save()
    return entry


def _sync_entries_for_author(api_base, author_id, node, author):
    entries_payload = fetch_remote_json(f"{api_base}/authors/{author_id}/entries/", node)
    if not isinstance(entries_payload, dict):
        return 0

    remote_entries = entries_payload.get("entries") or entries_payload.get("src") or []
    if not isinstance(remote_entries, list):
        return 0

    discovered_entries = 0
    for entry_payload in remote_entries:
        if not isinstance(entry_payload, dict):
            continue

        if entry_payload.get("visibility") not in ("PUBLIC", "UNLISTED", "FRIENDS", "DELETED"):
            continue

        if create_or_update_entry_from_remote_payload(entry_payload, author) is not None:
            discovered_entries += 1

    return discovered_entries


def sync_remote_authors_and_public_entries():
    discovered_authors = 0
    discovered_entries = 0

    for node in RemoteNode.objects.filter(is_active=True):
        api_base = normalize_url(node.api_base_url or f"{node.base_url}/api")
        authors_payload = fetch_remote_json(f"{api_base}/authors", node)
        if not isinstance(authors_payload, dict):
            continue
        authors = authors_payload.get("authors") or []
        if not isinstance(authors, list):
            continue

        for author_payload in authors:
            if not isinstance(author_payload, dict):
                continue
            author = upsert_remote_author(author_payload)
            if author is None:
                continue
            discovered_authors += 1

            parsed_author = parse_author_fqid(author.url)
            author_id = parsed_author["author_id"] if parsed_author else None
            if not author_id:
                continue

            discovered_entries += _sync_entries_for_author(
                api_base=api_base,
                author_id=author_id,
                node=node,
                author=author,
            )

    return {"authors": discovered_authors, "entries": discovered_entries}
