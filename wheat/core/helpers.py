from .models import EntryLike, CommentLike, Comment
from .serializers import EntrySerializer, AuthorSerializer, EntryLikeSerializer, CommentSerializer, CommentLikeSerializer

from .permissions import (
    get_requesting_author,
    filter_comments_for_viewer,
)

LIKES_PAGE_SIZE = 50

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
    base_url = request.build_absolute_uri("/").rstrip("/")
    return f"{base_url}/api/authors/{comment.entry.author.serial}/entries/{comment.entry.serial}/comments/{comment.serial}/likes/"

def build_entry_likes_url(request, entry):
    base_url = request.build_absolute_uri("/").rstrip("/")
    return f"{base_url}/api/authors/{entry.author.serial}/entries/{entry.serial}/likes/"

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
    base_url = request.build_absolute_uri("/").rstrip("/")
    html_web_url = f"{base_url}/authors/{entry.author.serial}/entries/{entry.serial}/"
    payload["web"] = html_web_url
    content_text = (entry.content or "").strip()
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

        base_url = request.build_absolute_uri("/").rstrip("/")
        comments_id = f"{base_url}/api/authors/{entry.author.serial}/entries/{entry.serial}/comments/"
        web_url = f"{base_url}/authors/{entry.author.serial}/entries/{entry.serial}/"

        payload["comments"] = {
            "type": "comments",
            "id": comments_id,
            "web": web_url,
            "page_number": page,
            "size": size,
            "count": visible_comments.count(),
            "src": comments_data,
        }

    return payload

def build_comment_payload(comment, request):
    comment_data = CommentSerializer(comment, context={"request": request}).data
    comment_data["entry"] = f"{request.build_absolute_uri('/').rstrip('/')}/api/authors/{comment.entry.author.serial}/entries/{comment.entry.serial}/"
    likes_qs = CommentLike.objects.filter(comment=comment).select_related("author").order_by("-published")
    comment_data["likes"] = build_likes_collection(
        likes_qs,
        CommentLikeSerializer,
        build_comment_likes_url(request, comment),
    )
    return comment_data

