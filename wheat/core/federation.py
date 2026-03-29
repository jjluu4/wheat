import logging

from .helpers import (
    normalize_url,
    send_json_to_remote_author_inbox,
)
from .models import Author, Entry

logger = logging.getLogger(__name__)


def remote_authors_for_entry(author, visibility):
    """
    PUBLIC: every known author on a *different* node (same host as poster excluded so
    co-locals already see the row locally). UNLISTED: accepted followers only.
    FRIENDS: mutual follows only.
    """
    followers = Author.objects.filter(
        following__target=author,
        following__status="ACCEPTED",
    ).exclude(host__contains="testserver")

    if visibility == "PUBLIC":
        poster_host = normalize_url(author.host or "")
        candidates = Author.objects.exclude(host__contains="testserver").exclude(pk=author.pk)
        if poster_host:
            recipients = [
                a
                for a in candidates
                if normalize_url(a.host or "") != poster_host
            ]
        else:
            recipients = list(followers)
        by_pk = {a.pk: a for a in recipients}
        return list(by_pk.values())

    if visibility == "UNLISTED":
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
    by `visibility` (PUBLIC -> all known foreign-node authors, UNLISTED -> followers,
    FRIENDS -> mutuals).
    """
    recipients = remote_authors_for_entry(author, visibility)
    failures = []
    for recipient in recipients:
        ok, error = send_to_author_inbox(recipient, payload, method=method)
        if not ok:
            logger.warning("Failed to deliver payload to %s: %s", recipient.url, error)
            failures.append({"target": recipient.url, "error": error})

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
