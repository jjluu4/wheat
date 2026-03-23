from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import uuid
import re

from ..auth import require_auth_for_view
from ..models import Author, Entry, Comment, EntryLike, CommentLike
from ..serializers import CommentLikeSerializer, EntryLikeSerializer
from ..permissions import (
    get_requesting_author,
    can_view_entry,
    can_view_comment,
)

from ..helpers import (
    get_pagination_params,
    LIKES_PAGE_SIZE,
    build_likes_collection,
    build_entry_likes_url,
    build_comment_likes_url,
    build_author_api_url,
    resolve_object_by_url,
)

ENTRY_OBJECT_RE = re.compile(r"/api/authors/(?P<author>[0-9a-f-]+)/entries/(?P<entry>[0-9a-f-]+)/?$")
COMMENT_OBJECT_RE = re.compile(r"/api/authors/(?P<author>[0-9a-f-]+)/commented/(?P<comment>[0-9a-f-]+)/?$")

def resolve_like_target(object_url):
    entry = resolve_object_by_url(Entry, object_url)
    if entry is not None:
        return "entry", entry

    comment = resolve_object_by_url(Comment, object_url)
    if comment is not None:
        return "comment", comment

    entry_match = ENTRY_OBJECT_RE.search(object_url or "")
    if entry_match:
        entry = get_object_or_404(
            Entry,
            serial=entry_match.group("entry"),
            author__serial=entry_match.group("author"),
        )
        return "entry", entry

    comment_match = COMMENT_OBJECT_RE.search(object_url or "")
    if comment_match:
        comment = get_object_or_404(
            Comment,
            serial=comment_match.group("comment"),
            author__serial=comment_match.group("author"),
        )
        return "comment", comment

    return None, None

def build_like_url(request, author, like_serial):
    return f"{build_author_api_url(author, request)}/liked/{like_serial}/"

def serialize_like_item(like):
    """Serialize either an EntryLike or CommentLike into its API representation."""
    if isinstance(like, EntryLike):
        return EntryLikeSerializer(like).data
    return CommentLikeSerializer(like).data


def build_mixed_likes_collection(items, collection_id, page, size):
    offset = (page - 1) * size
    page_items = items[offset : offset + size]
    return {
        "type": "likes",
        "id": collection_id,
        "web": collection_id.replace("/api/", "/", 1),
        "page_number": page,
        "size": size,
        "count": len(items),
        "src": [serialize_like_item(item) for item in page_items],
    }

@api_view(["GET", "POST"])
def author_liked(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)

    if request.method == "POST":
        require_auth_for_view(True)
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        requesting_author = get_requesting_author(request)
        if not requesting_author or requesting_author != author:
            return Response({"error": "Cannot like as another author"}, status=403)

        object_url = request.data.get("object")
        if not object_url:
            return Response({"error": "Object URL is required"}, status=400)

        target_type, target = resolve_like_target(object_url)
        if not target_type:
            return Response({"error": "Invalid object URL"}, status=400)

        if target_type == "entry":
            if not can_view_entry(target, requesting_author, request.user):
                return Response({"error": "You don't have permission to like this entry"}, status=403)

            existing_like = EntryLike.objects.filter(author=author, entry=target).select_related("author", "entry").first()
            if existing_like:
                return Response(EntryLikeSerializer(existing_like).data, status=200)

            like = EntryLike.objects.create(
                author=author,
                entry=target,
                url=build_like_url(request, author, uuid.uuid4()),
            )
            like.url = build_like_url(request, author, like.serial)
            like.save(update_fields=["url"])
            return Response(EntryLikeSerializer(like).data, status=201)

        if not can_view_comment(target, requesting_author, request.user):
            return Response({"error": "You don't have permission to like this comment"}, status=403)

        existing_like = CommentLike.objects.filter(author=author, comment=target).select_related("author", "comment").first()
        if existing_like:
            return Response(CommentLikeSerializer(existing_like).data, status=200)

        like = CommentLike.objects.create(
            author=author,
            comment=target,
            url=build_like_url(request, author, uuid.uuid4()),
        )
        like.url = build_like_url(request, author, like.serial)
        like.save(update_fields=["url"])
        return Response(CommentLikeSerializer(like).data, status=201)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    requesting_author = get_requesting_author(request)

    entry_likes = [
        like
        for like in EntryLike.objects.filter(author=author).select_related("author", "entry", "entry__author")
        if can_view_entry(like.entry, requesting_author, request.user)
    ]
    comment_likes = [
        like
        for like in CommentLike.objects.filter(author=author).select_related("author", "comment", "comment__entry", "comment__entry__author", "comment__author")
        if can_view_comment(like.comment, requesting_author, request.user)
    ]
    items = sorted(entry_likes + comment_likes, key=lambda like: like.published, reverse=True)

    collection_id = f"{build_author_api_url(author, request)}/liked/"
    return Response(build_mixed_likes_collection(items, collection_id, page, size))

@api_view(["GET"])
def entry_likes(request, author_serial, entry_serial):
    """API endpoint listing likes on a specific entry,"""
    require_auth_for_view(False) #handled manually
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    requesting_author = get_requesting_author(request)

    if not can_view_entry(entry, requesting_author, request.user):
        if not request.user.is_authenticated and entry.visibility == "FRIENDS":
            return Response({"error": "Authentication required"}, status=401)
        return Response({"error": "You don't have permission to view likes on this entry"}, status=403)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    likes_qs = EntryLike.objects.filter(entry=entry).select_related("author").order_by("-published")
    return Response(build_likes_collection(likes_qs, EntryLikeSerializer, build_entry_likes_url(request, entry), page, size))


@api_view(["GET"])
def comment_likes(request, author_serial, entry_serial, comment_serial):
    """API endpoint listing likes on a specific comment"""
    require_auth_for_view(False) #handled manually
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    comment = get_object_or_404(Comment, serial=comment_serial, entry=entry)
    requesting_author = get_requesting_author(request)

    if not can_view_comment(comment, requesting_author, request.user):
        if not request.user.is_authenticated and entry.visibility == "FRIENDS":
            return Response({"error": "Authentication required"}, status=401)
        return Response({"error": "You don't have permission to view likes on this comment"}, status=403)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    likes_qs = CommentLike.objects.filter(comment=comment).select_related("author").order_by("-published")
    return Response(build_likes_collection(likes_qs, CommentLikeSerializer, build_comment_likes_url(request, comment), page, size))
