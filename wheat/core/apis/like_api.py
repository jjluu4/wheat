from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
import uuid
import re
from ..auth import require_auth_for_view
from ..auth import is_remote_node_authenticated
from ..models import Author, Entry, Comment, EntryLike, CommentLike
from ..serializers import AuthorSerializer, CommentLikeSerializer, EntryLikeSerializer
from ..permissions import (get_requesting_author, can_view_entry, can_view_comment)
from ..helpers import (
    get_pagination_params,
    LIKES_PAGE_SIZE,
    build_likes_collection,
    build_entry_likes_url,
    build_comment_likes_url,
    build_author_api_url,
    normalize_url,
    resolve_object_by_url,
    send_json_to_remote_author_inbox,
    decode_fqid,
)
from ..federation import remote_authors_for_entry, send_to_author_inbox

ENTRY_OBJECT_RE = re.compile(r"/api/authors/(?P<author>[0-9a-f-]+)/entries/(?P<entry>[0-9a-f-]+)/?$")
COMMENT_OBJECT_RE = re.compile(r"/api/authors/(?P<author>[0-9a-f-]+)/commented/(?P<comment>[0-9a-f-]+)/?$")

def resolve_like_target(object_url):
    """Resolve a like target URL into (`entry`|`comment`, model_instance)."""
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


def choose_object_reference(requested_object_url, target):
    requested_raw = (requested_object_url or "").strip()
    canonical_raw = (getattr(target, "url", "") or "").strip()
    if not requested_raw:
        return canonical_raw
    if not canonical_raw:
        return requested_raw

    requested_normalized = normalize_url(requested_raw)
    canonical_normalized = normalize_url(canonical_raw)
    if requested_normalized == canonical_normalized:
        return canonical_raw
    return requested_raw

def build_like_url(request, author, like_serial):
    """Build a canonical API URL for a like object."""
    return f"{build_author_api_url(author, request)}/liked/{like_serial}/"


def post_json_to_remote_inbox(payload, inbox_author, timeout=5):
    """POST JSON to inbox_author's home node inbox (if remote)."""
    send_json_to_remote_author_inbox(getattr(inbox_author, "url", ""), payload, timeout=timeout)


def post_json_to_unique_author_inboxes(payload, authors, timeout=5):
    """POST JSON payload to unique authors' inboxes."""
    seen = set()
    for author in authors:
        aid = getattr(author, "id", None)
        if aid is None or aid in seen:
            continue
        seen.add(aid)
        post_json_to_remote_inbox(payload, author, timeout=timeout)


def forward_comment_like_to_entry_and_comment_authors(like_payload, comment):
    """
    Comment likes must reach both the commenter's node and the entry author's node
    (when different), so counts stay correct where the entry is canonical.
    """
    post_json_to_unique_author_inboxes(
        like_payload,
        authors=(comment.author, comment.entry.author),
    )


def distribute_activity_to_remote_followers(payload, entry_author, visibility):
    """Send an activity payload to remote followers who can see the entry."""
    recipients = remote_authors_for_entry(entry_author, visibility)
    for recipient in recipients:
        send_to_author_inbox(recipient, payload, method="POST")

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

def _author_liked_for_author(request, author):
    """Shared GET/POST likes collection logic for a resolved Author instance."""
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

        req_type = (request.data.get("type") or "like").lower()
        if req_type == "unlike":
            target_type, target = resolve_like_target(object_url)
            if not target_type:
                return Response({"error": "Invalid object URL"}, status=400)
            object_reference = choose_object_reference(object_url, target)
            if target_type == "entry":
                if not can_view_entry(target, requesting_author, request.user):
                    return Response({"error": "You don't have permission to unlike this entry"}, status=403)
                deleted, _ = EntryLike.objects.filter(author=author, entry=target).delete()
                if not deleted:
                    return Response({"error": "Like not found"}, status=404)
            else:
                if not can_view_comment(target, requesting_author, request.user):
                    return Response({"error": "You don't have permission to unlike this comment"}, status=403)
                deleted, _ = CommentLike.objects.filter(author=author, comment=target).delete()
                if not deleted:
                    return Response({"error": "Like not found"}, status=404)

            unlike_id = f"{normalize_url(author.url)}/unlikes/{uuid.uuid4()}"
            unlike_payload = {
                "type": "unlike",
                "id": unlike_id,
                "author": AuthorSerializer(author).data,
                "object": object_reference,
            }
            if target_type == "entry":
                post_json_to_remote_inbox(unlike_payload, target.author)
                distribute_activity_to_remote_followers(unlike_payload, target.author, target.visibility)
            else:
                forward_comment_like_to_entry_and_comment_authors(unlike_payload, target)
                distribute_activity_to_remote_followers(
                    unlike_payload, target.entry.author, target.entry.visibility
                )
            return Response({"type": "unlike", "object": object_reference}, status=200)

        target_type, target = resolve_like_target(object_url)
        if not target_type:
            return Response({"error": "Invalid object URL"}, status=400)

        if target_type == "entry":
            if not can_view_entry(target, requesting_author, request.user):
                return Response({"error": "You don't have permission to like this entry"}, status=403)

            object_reference = choose_object_reference(object_url, target)

            existing_like = EntryLike.objects.filter(author=author, entry=target).select_related("author", "entry").first()
            if existing_like:
                existing_data = EntryLikeSerializer(existing_like).data
                existing_data["object"] = object_reference
                return Response(existing_data, status=200)

            try:
                like = EntryLike.objects.create(
                    author=author,
                    entry=target,
                    url=build_like_url(request, author, uuid.uuid4()),
                )
            except IntegrityError:
                existing_like = EntryLike.objects.select_related("author", "entry").get(author=author, entry=target)
                return Response(EntryLikeSerializer(existing_like).data, status=200)
            like.url = build_like_url(request, author, like.serial)
            like.save(update_fields=["url"])
            response_data = EntryLikeSerializer(like).data
            response_data.setdefault("type", "like")
            response_data["object"] = object_reference
            post_json_to_remote_inbox(response_data, target.author)
            distribute_activity_to_remote_followers(
                response_data, target.author, target.visibility
            )
            return Response(response_data, status=201)

        if not can_view_comment(target, requesting_author, request.user):
            return Response({"error": "You don't have permission to like this comment"}, status=403)

        

        object_reference = choose_object_reference(object_url, target)

        existing_like = CommentLike.objects.filter(author=author, comment=target).select_related("author", "comment").first()
        if existing_like:
            existing_data = CommentLikeSerializer(existing_like).data
            existing_data["object"] = object_reference
            return Response(existing_data, status=200)

        try:
            like = CommentLike.objects.create(
                author=author,
                comment=target,
                url=build_like_url(request, author, uuid.uuid4()),
            )
        except IntegrityError:
            existing_like = CommentLike.objects.select_related("author", "comment").get(author=author, comment=target)
            return Response(CommentLikeSerializer(existing_like).data, status=200)
        like.url = build_like_url(request, author, like.serial)
        like.save(update_fields=["url"])
        response_data = CommentLikeSerializer(like).data
        response_data.setdefault("type", "like")
        response_data["object"] = object_reference
        forward_comment_like_to_entry_and_comment_authors(response_data, target)
        distribute_activity_to_remote_followers(
            response_data, target.entry.author, target.entry.visibility
        )
        return Response(response_data, status=201)

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


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication])
def author_liked(request, author_serial):
    """GET/POST likes collection for an author.

    POST supports both `type=like` and `type=unlike` to create or remove likes,
    and mirrors those changes to relevant remote inboxes.
    """
    author = get_object_or_404(Author, serial=author_serial)
    return _author_liked_for_author(request, author)


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication])
def author_liked_fqid(request, author_fqid):
    """Same as author_liked but author is identified by full URL (path segment)."""
    author = resolve_object_by_url(Author, decode_fqid(author_fqid))
    if author is None:
        return Response({"error": "Author not found"}, status=404)
    return _author_liked_for_author(request, author)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def entry_likes(request, author_serial, entry_serial):
    """API endpoint listing likes on a specific entry,"""
    require_auth_for_view(False) #handled manually
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    requesting_author = get_requesting_author(request)

    if not can_view_entry(entry, requesting_author, request.user):
        if not request.user.is_authenticated and not is_remote_node_authenticated(request) and entry.visibility == "FRIENDS":
            return Response({"error": "Authentication required"}, status=401)
        return Response({"error": "You don't have permission to view likes on this entry"}, status=403)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    likes_qs = EntryLike.objects.filter(entry=entry).select_related("author").order_by("-published")
    return Response(build_likes_collection(likes_qs, EntryLikeSerializer, build_entry_likes_url(request, entry), page, size))


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def entry_likes_fqid(request, entry_fqid):
    """List likes on an entry identified by full URL (same behavior as entry_likes)."""
    require_auth_for_view(False)
    entry = resolve_object_by_url(Entry, decode_fqid(entry_fqid))
    if entry is None:
        return Response({"error": "Entry not found"}, status=404)

    requesting_author = get_requesting_author(request)
    if not can_view_entry(entry, requesting_author, request.user):
        if not request.user.is_authenticated and not is_remote_node_authenticated(request) and entry.visibility == "FRIENDS":
            return Response({"error": "Authentication required"}, status=401)
        return Response({"error": "You don't have permission to view likes on this entry"}, status=403)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    likes_qs = EntryLike.objects.filter(entry=entry).select_related("author").order_by("-published")
    return Response(build_likes_collection(likes_qs, EntryLikeSerializer, build_entry_likes_url(request, entry), page, size))


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def like_fqid(request, like_fqid):
    """Retrieve a single entry like or comment like by its canonical URL."""
    require_auth_for_view(False)
    decoded = decode_fqid(like_fqid)
    entry_like = resolve_object_by_url(EntryLike, decoded)
    if entry_like is not None:
        requesting_author = get_requesting_author(request)
        entry = entry_like.entry
        if not can_view_entry(entry, requesting_author, request.user):
            if not request.user.is_authenticated and not is_remote_node_authenticated(request) and entry.visibility == "FRIENDS":
                return Response({"error": "Authentication required"}, status=401)
            return Response({"error": "You don't have permission to view this like"}, status=403)
        return Response(EntryLikeSerializer(entry_like).data)

    comment_like = resolve_object_by_url(CommentLike, decoded)
    if comment_like is not None:
        requesting_author = get_requesting_author(request)
        comment = comment_like.comment
        entry = comment.entry
        if not can_view_comment(comment, requesting_author, request.user):
            if not request.user.is_authenticated and not is_remote_node_authenticated(request) and entry.visibility == "FRIENDS":
                return Response({"error": "Authentication required"}, status=401)
            return Response({"error": "You don't have permission to view this like"}, status=403)
        return Response(CommentLikeSerializer(comment_like).data)

    return Response({"error": "Like not found"}, status=404)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def comment_likes(request, author_serial, entry_serial, comment_serial):
    """API endpoint listing likes on a specific comment"""
    require_auth_for_view(False) #handled manually
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    comment = get_object_or_404(Comment, serial=comment_serial, entry=entry)
    requesting_author = get_requesting_author(request)

    if not can_view_comment(comment, requesting_author, request.user):
        if not request.user.is_authenticated and not is_remote_node_authenticated(request) and entry.visibility == "FRIENDS":
            return Response({"error": "Authentication required"}, status=401)
        return Response({"error": "You don't have permission to view likes on this comment"}, status=403)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    likes_qs = CommentLike.objects.filter(comment=comment).select_related("author").order_by("-published")
    return Response(build_likes_collection(likes_qs, CommentLikeSerializer, build_comment_likes_url(request, comment), page, size))
