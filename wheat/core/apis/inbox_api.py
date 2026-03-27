import json
import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from ..auth import is_remote_node_authenticated
from ..helpers import build_comment_payload, build_entry_payload, normalize_url, resolve_object_by_url
from ..models import Author, Comment, CommentLike, Entry, EntryLike, Follow, InboxItem


def parse_remote_published(payload):
    published_raw = (payload.get("published") or "").strip()
    if not published_raw:
        return None

    parsed = parse_datetime(published_raw)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def create_or_update_author(author_payload, request):
    if not isinstance(author_payload, dict):
        return None

    remote_id = (author_payload.get("id") or "").strip()
    if not remote_id:
        return None

    author = resolve_object_by_url(Author, remote_id)
    if author is None:
        serial = uuid.uuid4()
        base = normalize_url(request.build_absolute_uri("/"))
        author = Author.objects.create(
            serial=serial,
            url=remote_id,
            host=author_payload.get("host") or "",
            displayName=author_payload.get("displayName") or "Remote Author",
            github=author_payload.get("github") or "",
            profileImage=author_payload.get("profileImage") or "",
            web=author_payload.get("web") or f"{base}/authors/{serial}",
            description=author_payload.get("description") or "",
        )
        return author

    changed = False
    for field in ("host", "displayName", "github", "profileImage", "web"):
        incoming = author_payload.get(field)
        if incoming is not None and getattr(author, field) != incoming:
            setattr(author, field, incoming)
            changed = True
    if changed:
        author.save()
    return author


def create_or_update_entry(payload, request):
    entry_id = (payload.get("id") or "").strip()
    if not entry_id:
        return None, "Entry id is required"

    author = create_or_update_author(payload.get("author"), request)
    if author is None:
        return None, "Entry author is required"

    entry = resolve_object_by_url(Entry, entry_id)
    create = entry is None
    if create:
        entry = Entry(author=author, url=entry_id)

    entry.author = author
    entry.url = entry_id
    entry.title = (payload.get("title") or "").strip() or "Untitled"
    entry.content = payload.get("content") or ""
    entry.content_type = payload.get("contentType", payload.get("content_type", "text/plain"))
    entry.image_url = payload.get("imageUrl", payload.get("image_url", "")) or ""
    entry.visibility = payload.get("visibility") if payload.get("visibility") in ("PUBLIC", "UNLISTED", "FRIENDS", "DELETED") else "PUBLIC"
    published = parse_remote_published(payload)
    if published is not None:
        entry.published = published
    entry.web = payload.get("web") or entry.web or ""
    if not entry.web:
        base = normalize_url(request.build_absolute_uri("/"))
        entry.web = f"{base}/authors/{author.serial}/entries/{entry.serial}"
    entry.save()
    return entry, None


def create_or_update_comment(payload, request):
    comment_id = (payload.get("id") or "").strip()
    if not comment_id:
        return None, "Comment id is required"

    author = create_or_update_author(payload.get("author"), request)
    if author is None:
        return None, "Comment author is required"

    entry_url = (payload.get("entry") or "").strip()
    entry = resolve_object_by_url(Entry, entry_url)
    if entry is None:
        return None, "Comment entry target not found"

    comment = resolve_object_by_url(Comment, comment_id)
    create = comment is None
    if create:
        comment = Comment(author=author, entry=entry, url=comment_id)

    comment.author = author
    comment.entry = entry
    comment.url = comment_id
    comment.content = payload.get("comment", payload.get("content", ""))
    comment.content_type = payload.get("contentType", payload.get("content_type", "text/plain"))
    published = parse_remote_published(payload)
    if published is not None:
        comment.published = published
    comment.save()
    return comment, None


def create_or_update_follow(payload, request, inbox_owner):
    """Create/update a Follow row from a remote follow inbox event."""
    actor = create_or_update_author(payload.get("actor"), request)
    object_author_payload = payload.get("object")
    object_id = object_author_payload.get("id") if isinstance(object_author_payload, dict) else ""
    if actor is None or not object_id:
        return None, "Follow actor and object are required"

    object_author = resolve_object_by_url(Author, object_id)
    if object_author is None:
        object_author = inbox_owner

    follow, _ = Follow.objects.get_or_create(actor=actor, target=object_author, defaults={"status": "REQUESTED"})
    if follow.status == "REJECTED":
        follow.status = "REQUESTED"
        follow.save(update_fields=["status"])
    return follow, None


def delete_follow_from_unfollow_payload(payload, request, inbox_owner):
    """
    Remove Follow(actor, target) using actor + object from the payload.
    inbox_owner identifies which inbox received the event (may be followee or follower node).
    """
    actor_payload = payload.get("actor")
    if not isinstance(actor_payload, dict):
        return None, "Unfollow actor is required"
    actor_id = (actor_payload.get("id") or "").strip()
    actor = resolve_object_by_url(Author, actor_id) or create_or_update_author(actor_payload, request)
    if actor is None:
        return None, "Unfollow actor is required"

    object_payload = payload.get("object")
    object_id = (object_payload.get("id") or "").strip() if isinstance(object_payload, dict) else ""
    target = resolve_object_by_url(Author, object_id) if object_id else None
    if target is None:
        target = inbox_owner

    Follow.objects.filter(actor=actor, target=target).delete()
    return None, None


def create_or_update_like(payload, request):
    """Create/update an entry/comment like from a remote inbox event."""
    author = create_or_update_author(payload.get("author"), request)
    if author is None:
        return None, "Like author is required"

    object_url = (payload.get("object") or "").strip()
    if not object_url:
        return None, "Like object is required"

    entry = resolve_object_by_url(Entry, object_url)
    if entry is not None:
        published = parse_remote_published(payload)
        like, _ = EntryLike.objects.get_or_create(
            author=author,
            entry=entry,
            defaults={
                "url": payload.get("id") or f"{normalize_url(author.url)}/liked/{uuid.uuid4()}",
                "published": published or timezone.now(),
            },
        )
        if not like.url:
            like.url = payload.get("id") or f"{normalize_url(author.url)}/liked/{like.serial}"
        if published is not None:
            like.published = published
        like.save(update_fields=["url", "published"] if published is not None else ["url"])
        return like, None

    comment = resolve_object_by_url(Comment, object_url)
    if comment is not None:
        published = parse_remote_published(payload)
        like, _ = CommentLike.objects.get_or_create(
            author=author,
            comment=comment,
            defaults={
                "url": payload.get("id") or f"{normalize_url(author.url)}/liked/{uuid.uuid4()}",
                "published": published or timezone.now(),
            },
        )
        if not like.url:
            like.url = payload.get("id") or f"{normalize_url(author.url)}/liked/{like.serial}"
        if published is not None:
            like.published = published
        like.save(update_fields=["url", "published"] if published is not None else ["url"])
        return like, None

    return None, "Like object target not found"


def delete_like_from_inbox(payload, request):
    """Remove an entry/comment like from a remote unlike inbox event."""
    author = create_or_update_author(payload.get("author"), request)
    if author is None:
        return None, "Like author is required"

    object_url = (payload.get("object") or "").strip()
    if not object_url:
        return None, "Like object is required"

    entry = resolve_object_by_url(Entry, object_url)
    if entry is not None:
        EntryLike.objects.filter(author=author, entry=entry).delete()
        return None, None

    comment = resolve_object_by_url(Comment, object_url)
    if comment is not None:
        CommentLike.objects.filter(author=author, comment=comment).delete()
        return None, None

    return None, "Like object target not found"


def build_item_id_from_payload(payload):
    payload_type = (payload.get("type") or "unknown").lower()
    if payload_type == "entry":
        dedup_payload = {
            "type": payload_type,
            "id": payload.get("id") or "",
            "title": payload.get("title") or "",
            "content": payload.get("content") or "",
            "contentType": payload.get("contentType", payload.get("content_type", "")) or "",
            "imageUrl": payload.get("imageUrl", payload.get("image_url", "")) or "",
            "visibility": payload.get("visibility") or "",
            "published": payload.get("published") or "",
            "web": payload.get("web") or "",
        }
        generated = uuid.uuid5(
            uuid.NAMESPACE_URL,
            json.dumps(dedup_payload, sort_keys=True, separators=(",", ":")),
        )
        return f"https://inbox.local/events/{payload_type}/{generated}"

    payload_id = (payload.get("id") or "").strip()
    if payload_id:
        return payload_id

    generated = uuid.uuid5(
        uuid.NAMESPACE_URL,
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str),
    )
    return f"https://inbox.local/events/{payload_type}/{generated}"


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
def inbox_item(request, author_serial):
    """Remote inbox endpoint for federated activity delivery.
    """
    inbox_owner = get_object_or_404(Author, serial=author_serial)

    if not is_remote_node_authenticated(request):
        return Response({"error": "Authentication required"}, status=401)

    payload = request.data if isinstance(request.data, dict) else {}
    object_type = (payload.get("type") or "").lower()
    if object_type not in {"entry", "follow", "like", "comment", "accept", "unfollow", "unlike"}:
        return Response({"error": "Unsupported inbox object type"}, status=400)

    event_id = build_item_id_from_payload(payload)
    '''
    if InboxItem.objects.filter(owner=inbox_owner, item_id=event_id).exists():
        return Response({"type": object_type, "status": "already-processed"}, status=200)
    '''

    if object_type == "accept":
        actor_payload = payload.get("actor")
        followee_id = (actor_payload.get("id") or "").strip() if isinstance(actor_payload, dict) else ""
        followee = resolve_object_by_url(Author, followee_id) or create_or_update_author(actor_payload, request)
        if followee is None:
            return Response({"error": "Accept actor (the one who accepted) is required"}, status=400)
        follow = Follow.objects.filter(actor=inbox_owner, target=followee).first()
        if follow is None:
            follow, _ = Follow.objects.get_or_create(
                actor=inbox_owner,
                target=followee,
                defaults={"status": "ACCEPTED"},
            )
        if follow.status != "ACCEPTED":
            follow.status = "ACCEPTED"
            follow.save(update_fields=["status"])
        InboxItem.objects.create(
            owner=inbox_owner,
            item_type=object_type,
            item_id=event_id,
            payload=payload,
        )
        return Response({"type": "accept", "status": "accepted"}, status=201)

    if object_type == "unfollow":
        _, error = delete_follow_from_unfollow_payload(payload, request, inbox_owner)
        if error:
            return Response({"error": error}, status=400)
        response = Response({"type": "unfollow", "status": "removed"}, status=201)
        InboxItem.objects.create(
            owner=inbox_owner,
            item_type=object_type,
            item_id=event_id,
            payload=payload,
        )
        return response

    if object_type == "unlike":
        _, error = delete_like_from_inbox(payload, request)
        if error:
            return Response({"error": error}, status=400)
        response = Response({"type": "unlike", "status": "removed"}, status=201)
        InboxItem.objects.create(
            owner=inbox_owner,
            item_type=object_type,
            item_id=event_id,
            payload=payload,
        )
        return response

    if object_type == "entry":
        entry, error = create_or_update_entry(payload, request)
        if error:
            return Response({"error": error}, status=400)
        response = Response(build_entry_payload(entry, request), status=201)
    elif object_type == "comment":
        comment, error = create_or_update_comment(payload, request)
        if error:
            return Response({"error": error}, status=400)
        response = Response(build_comment_payload(comment, request), status=201)
    elif object_type == "follow":
        follow, error = create_or_update_follow(payload, request, inbox_owner)
        if error:
            return Response({"error": error}, status=400)
        response = Response(
            {
                "type": "follow",
                "summary": f"{follow.actor.displayName} wants to follow {follow.target.displayName}",
            },
            status=201,
        )
    else:
        like, error = create_or_update_like(payload, request)
        if error:
            return Response({"error": error}, status=400)
        data = {"type": "like", "id": like.url, "object": payload.get("object")}
        response = Response(data, status=201)
    
    if InboxItem.objects.filter(owner=inbox_owner, item_id=event_id).exists():
        return Response({"type": object_type, "status": "already-processed"}, status=200)
    else:
        InboxItem.objects.create(
            owner=inbox_owner,
            item_type=object_type,
            item_id=event_id,
            payload=payload,
        )        
    return response
