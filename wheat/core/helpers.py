from .models import EntryLike, CommentLike, Comment
from .serializers import EntrySerializer, AuthorSerializer, EntryLikeSerializer, CommentSerializer, CommentLikeSerializer

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
