from .models import EntryLike
from .serializers import EntrySerializer, AuthorSerializer, EntryLikeSerializer

LIKES_PAGE_SIZE = 50

def get_pagination_params(request, default_size=5):
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
    return {
        "type": "likes",
        "id": collection_id,
        "page_number": page,
        "size": size,
        "count": total,
        "src": serializer_class(page_items, many=True).data,
    }

def build_entry_payload(entry, request):
    payload = EntrySerializer(entry).data
    payload["author"] = AuthorSerializer(entry.author).data
    likes_qs = EntryLike.objects.filter(entry=entry).select_related("author").order_by("-published")
    payload["likes"] = build_likes_collection(
        likes_qs,
        EntryLikeSerializer,
        build_entry_likes_url(request, entry),
    )
    return payload

