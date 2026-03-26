import logging
from .helpers import normalize_url, parse_author_fqid, send_json_to_remote_author_inbox
from .models import Author, Entry, Follow, RemoteNode

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

            parsed_author = parse_author_fqid(author.url)
            author_id = parsed_author["author_id"] if parsed_author else None
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
