from django.db.models import Q

from .models import Author, EntryLike, CommentLike, Comment
from .serializers import EntrySerializer, AuthorSerializer, EntryLikeSerializer, CommentSerializer, CommentLikeSerializer
from rest_framework.response import Response
import urllib
import requests

from .auth import add_auth_headers
from .models import RemoteNode, Entry, Author

from .permissions import (
    get_requesting_author,
    filter_comments_for_viewer,
)

LIKES_PAGE_SIZE = 50


def normalize_url(value):
    """Normalize a URL for comparison/building without changing its identity."""
    value = (value or "").strip()
    if not value:
        return ""
    return value.rstrip("/")


def url_variants(value):
    """Return trailing-slash variants for exact URL matching in stored FQIDs."""
    raw = (value or "").strip()
    normalized = normalize_url(raw)
    if not normalized:
        return []

    variants = []
    for candidate in (raw, normalized, f"{normalized}/"):
        if candidate and candidate not in variants:
            variants.append(candidate)
    return variants


def resolve_object_by_url(model, object_url):
    variants = url_variants(object_url)
    if not variants:
        return None
    return model.objects.filter(url__in=variants).first()


def decode_fqid(value):
    """Decode a percent-encoded FQID without changing its identity."""
    return urllib.parse.unquote((value or "").strip())


def parse_author_fqid(author_fqid):
    """
    Parse an author FQID into reusable pieces.

    Returns None when the value is not a valid absolute author URL.
    """
    decoded = decode_fqid(author_fqid)
    parsed = urllib.parse.urlparse(decoded)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None

    path_parts = [part for part in parsed.path.split("/") if part]
    for idx, part in enumerate(path_parts):
        if part == "authors" and idx + 1 < len(path_parts):
            author_id = path_parts[idx + 1]
            api_path = "/" + "/".join(path_parts[:idx]) if idx > 0 else ""
            api_base = normalize_url(f"{parsed.scheme}://{parsed.netloc}{api_path}")
            base_url = normalize_url(f"{parsed.scheme}://{parsed.netloc}")
            web_base = api_base[:-4] if api_base.endswith("/api") else base_url
            return {
                "fqid": normalize_url(decoded),
                "author_id": author_id,
                "api_base": api_base,
                "base_url": base_url,
                "web_base": normalize_url(web_base),
            }
    return None


def find_remote_node_for_author_fqid(author_fqid):
    """Find the configured remote node that should be used for an author FQID."""
    parts = parse_author_fqid(author_fqid)
    if not parts:
        return None

    api_variants = url_variants(parts["api_base"])
    base_variants = url_variants(parts["base_url"])
    return (
        RemoteNode.objects.filter(is_active=True)
        .filter(Q(api_base_url__in=api_variants) | Q(base_url__in=base_variants))
        .first()
    )


def build_remote_author_inbox_url(author_fqid):
    """Derive a remote inbox URL from an author FQID."""
    parts = parse_author_fqid(author_fqid)
    if not parts:
        return None
    return f"{parts['api_base']}/authors/{parts['author_id']}/inbox"


def send_json_to_remote_author_inbox(author_fqid, payload, method="POST", timeout=10):
    """Send JSON to a remote author's inbox using configured node credentials."""
    normalized_fqid = normalize_url(author_fqid)
    if not normalized_fqid or "testserver" in normalized_fqid:
        return True, None

    remote_node = find_remote_node_for_author_fqid(normalized_fqid)
    if remote_node is None:
        return False, f"No active remote node credentials configured for {normalized_fqid}"

    inbox_url = build_remote_author_inbox_url(normalized_fqid)
    if not inbox_url:
        return False, "Remote author URL is invalid; could not derive inbox URL"

    request_fn = {
        "POST": requests.post,
    }.get(method.upper())
    if request_fn is None:
        return False, f"Unsupported method {method}"

    headers = add_auth_headers({"Content-Type": "application/json"}, remote_node)
    try:
        response = request_fn(inbox_url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        return False, f"Failed to reach remote inbox: {exc}"

    if response.status_code < 200 or response.status_code >= 300:
        return False, f"Remote inbox rejected request with status {response.status_code}"

    return True, None


def fetch_remote_json(url, remote_node, timeout=10):
    """Fetch JSON from a configured remote node using Basic Auth."""
    headers = {
        "Accept": "application/json",
        "User-Agent": "SocialDistribution/1.0",
    }
    headers = add_auth_headers(headers, remote_node)

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    try:
        payload = response.json()
    except ValueError:
        return None

    return payload if isinstance(payload, dict) else None


def upsert_remote_author(author_payload, fallback_fqid=None):
    """Create or update a canonical local Author row from remote author data."""
    payload = author_payload if isinstance(author_payload, dict) else {}
    author_fqid = normalize_url(payload.get("id") or payload.get("url") or fallback_fqid or "")
    parts = parse_author_fqid(author_fqid)
    if not author_fqid or not parts:
        return None

    author = resolve_object_by_url(Author, author_fqid)
    if author is None:
        author = Author(url=author_fqid)

    author.url = author_fqid
    author.host = normalize_url(payload.get("host") or parts["api_base"])
    author.displayName = payload.get("displayName") or author.displayName or parts["author_id"] or "Remote Author"
    author.github = payload.get("github") or getattr(author, "github", "") or ""
    author.profileImage = payload.get("profileImage") or getattr(author, "profileImage", "") or ""
    author.web = payload.get("web") or getattr(author, "web", "") or f"{parts['web_base']}/authors/{parts['author_id']}"
    author.description = payload.get("description") or getattr(author, "description", "") or ""
    author.save()
    return author


def resolve_remote_author(author_fqid, allow_stub=True):
    """
    Resolve an author FQID into a local Author row, fetching or stubbing as needed.
    """
    decoded_fqid = decode_fqid(author_fqid)
    author = resolve_object_by_url(Author, decoded_fqid)
    if author is not None:
        return author

    remote_node = find_remote_node_for_author_fqid(decoded_fqid)
    if remote_node is not None:
        payload = fetch_remote_json(decoded_fqid, remote_node)
        if payload:
            return upsert_remote_author(payload, fallback_fqid=decoded_fqid)

    if not allow_stub or remote_node is None:
        return None

    parts = parse_author_fqid(decoded_fqid)
    if not parts:
        return None

    return upsert_remote_author(
        {
            "id": parts["fqid"],
            "host": parts["api_base"],
            "displayName": parts["author_id"],
            "web": f"{parts['web_base']}/authors/{parts['author_id']}",
        },
        fallback_fqid=decoded_fqid,
    )


def build_author_api_url(author, request=None):
    api_root = normalize_url(getattr(author, "host", ""))
    if api_root:
        return f"{api_root}/authors/{author.serial}"

    stored = normalize_url(getattr(author, "url", ""))
    if stored.startswith("http://") or stored.startswith("https://"):
        return stored

    if request is not None:
        return f"{normalize_url(request.build_absolute_uri('/'))}/api/authors/{author.serial}"
    return stored


def build_author_web_url(author, request=None):
    stored = normalize_url(getattr(author, "web", ""))
    if stored.startswith("http://") or stored.startswith("https://"):
        return stored

    api_root = normalize_url(getattr(author, "host", ""))
    if api_root.endswith("/api"):
        return f"{api_root[:-4]}/authors/{author.serial}"

    if request is not None:
        return f"{normalize_url(request.build_absolute_uri('/'))}/authors/{author.serial}"
    return stored


def build_entry_api_url(entry, request=None):
    stored = (getattr(entry, "url", "") or "").strip()
    if stored.startswith("http://") or stored.startswith("https://"):
        return stored
    return f"{build_author_api_url(entry.author, request)}/entries/{entry.serial}"


def build_entry_web_url(entry, request=None):
    return f"{build_author_web_url(entry.author, request)}/entries/{entry.serial}/"


def build_comment_api_url(comment, request=None):
    stored = (getattr(comment, "url", "") or "").strip()
    if stored.startswith("http://") or stored.startswith("https://"):
        return stored
    return f"{build_author_api_url(comment.author, request)}/commented/{comment.serial}"


def build_comment_web_url(comment, request=None):
    return f"{build_author_web_url(comment.author, request)}/comments/{comment.serial}"


def build_author_commented_collection_id(author, request=None):
    return f"{build_author_api_url(author, request)}/commented/"


def build_author_commented_collection_web(author, request=None):
    return f"{build_author_web_url(author, request)}/comments/"


def build_entry_comments_collection_id(entry, request=None):
    return f"{normalize_url(build_entry_api_url(entry, request))}/comments/"

def get_pagination_params(request, default_size=5):
    """Parse page/size query params and return sanitized pagination values."""
    try:
        page = int(request.GET.get("page", 1))
        if page < 1:
            page = 1
    except (TypeError, ValueError):
        page = 1

    try:
        size = int(request.GET.get("size", default_size))
        if size < 1:
            size = default_size
    except (TypeError, ValueError):
        size = default_size

    return page, size

def build_comment_likes_url(request, comment):
    return f"{normalize_url(build_entry_api_url(comment.entry, request))}/comments/{comment.serial}/likes/"

def build_entry_likes_url(request, entry):
    return f"{normalize_url(build_entry_api_url(entry, request))}/likes/"

def build_likes_collection(queryset, serializer_class, collection_id, page=1, size=LIKES_PAGE_SIZE):
    offset = (page - 1) * size
    total = queryset.count()
    page_items = list(queryset[offset : offset + size])
    web_url = collection_id.replace("/api/", "/")
    return {
        "type": "likes",
        "id": collection_id,
        "web": web_url,
        "page_number": page,
        "size": size,
        "count": total,
        "src": serializer_class(page_items, many=True).data,
    }

def build_entry_payload(entry, request):
    """Build the full API payload for an entry, including author, likes, and initial comments."""
    payload = EntrySerializer(entry).data
    payload["author"] = AuthorSerializer(entry.author).data
    payload["web"] = build_entry_web_url(entry, request)
    content_text = (entry.content or "").strip()
    payload["description"] = ""
    if content_text:
        payload["description"] = (content_text[:197] + "...") if len(content_text) > 200 else content_text

    likes_qs = EntryLike.objects.filter(entry=entry).select_related("author").order_by("-published")
    payload["likes"] = build_likes_collection(
        likes_qs,
        EntryLikeSerializer,
        build_entry_likes_url(request, entry),
    )

    # Embed a first page of comments when the viewer is allowed to see them
    requesting_author = get_requesting_author(request)
    visible_comments = filter_comments_for_viewer(
        Comment.objects.filter(entry=entry).select_related("author", "entry__author").order_by("-published"),
        entry,
        requesting_author,
        request.user,
    )

    if visible_comments.exists():
        page = 1
        size = 5
        page_comments = list(visible_comments[:size])
        comments_data = [build_comment_payload(comment, request) for comment in page_comments]

        payload["comments"] = {
            "type": "comments",
            "id": build_entry_comments_collection_id(entry, request),
            "web": build_entry_web_url(entry, request),
            "page_number": page,
            "size": size,
            "count": visible_comments.count(),
            "src": comments_data,
        }

    return payload

def build_comment_payload(comment, request):
    comment_data = CommentSerializer(comment, context={"request": request}).data
    comment_data["entry"] = build_entry_api_url(comment.entry, request)
    comment_data["web"] = build_comment_web_url(comment, request)
    likes_qs = CommentLike.objects.filter(comment=comment).select_related("author").order_by("-published")
    comment_data["likes"] = build_likes_collection(
        likes_qs,
        CommentLikeSerializer,
        build_comment_likes_url(request, comment),
    )
    return comment_data

def fetch_remote_resource(fqid):
    decoded_fqid = decode_fqid(fqid)

    if not decoded_fqid.startswith(('http://', 'https://')):
        decoded_fqid = 'http://' + decoded_fqid

    parsed_url = urllib.parse.urlparse(decoded_fqid)
    if not parsed_url.netloc:
        return Response({"error": "Invalid FQID format"},status=400)

    remote_host = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    try:
        remote_node = (
            find_remote_node_for_author_fqid(decoded_fqid)
            or RemoteNode.objects.get(base_url=remote_host, is_active=True)
        )

        payload = fetch_remote_json(decoded_fqid, remote_node)
        if payload is not None:
            return Response(payload)

        response = requests.get(
            decoded_fqid,
            headers=add_auth_headers(
                {'Accept': 'application/json','User-Agent': 'SocialDistribution/1.0'},
                remote_node,
            ),
            timeout=10
        )

        if response.status_code == 404:
            return Response({"error": "Resource not found on remote node"}, status=404)
        else:
            return Response({"error": f"Remote node returned status {response.status_code}"},status=502)

    except RemoteNode.DoesNotExist:
        return Response({"error": "Remote node not configured or inactive"},status=400)

    except requests.exceptions.RequestException as e:
        return Response({"error": f"Failed to connect to remote node: {str(e)}"},status=503)

def find_remote_node_by_url(url):
    """Find an active RemoteNode whose base_url is a prefix of the given URL, returns None if no matching node is found"""
    normalized = normalize_url(url)
    for node in RemoteNode.objects.filter(is_active=True):
        node_base = normalize_url(node.base_url)
        if normalized.startswith(node_base):
            return node
    return None

def get_or_fetch_remote_entry(entry_url, request=None):
    """
    Return an Entry instance for the given URL
    - if not local, fetch from remote node and store
    - returns None if the entry cannot be fetched/invalid
    """
    from .federation import create_or_update_entry_from_remote_payload, upsert_remote_author

    entry = resolve_object_by_url(Entry, entry_url) # try to resolve locally
    if entry is not None:
        return entry

    remote_node = find_remote_node_by_url(entry_url) # try to resolve remotely
    if remote_node is None:
        return None

    payload = fetch_remote_json(entry_url, remote_node)
    if not isinstance(payload, dict):
        return None

    author_payload = payload.get('author')
    if not author_payload:
        return None

    author = upsert_remote_author(author_payload) # create/update local author record

    return create_or_update_entry_from_remote_payload(payload, author) # create/update entry