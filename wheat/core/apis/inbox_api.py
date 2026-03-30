import json, base64
import re
import uuid

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.files.base import ContentFile
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from ..auth import require_remote_node_auth
from ..helpers import build_comment_payload, build_entry_payload, normalize_url, resolve_object_by_url
from ..models import Author, Comment, CommentLike, Entry, EntryLike, Follow, InboxItem, Image


ENTRY_OBJECT_RE = re.compile(r"/api/authors/(?P<author>[0-9a-f-]+)/entries/(?P<entry>[0-9a-f-]+)/?$")
COMMENT_OBJECT_RE = re.compile(r"/api/authors/(?P<author>[0-9a-f-]+)/commented/(?P<comment>[0-9a-f-]+)/?$")


def resolve_like_object_for_inbox(object_url):
    """Resolve like targets by exact URL first, then by UUIDs embedded in canonical API paths."""
    entry = resolve_object_by_url(Entry, object_url)
    if entry is not None:
        return "entry", entry

    comment = resolve_object_by_url(Comment, object_url)
    if comment is not None:
        return "comment", comment

    entry_match = ENTRY_OBJECT_RE.search((object_url or "").strip())
    if entry_match:
        entry = Entry.objects.filter(
            serial=entry_match.group("entry"),
            author__serial=entry_match.group("author"),
        ).first()
        if entry is not None:
            return "entry", entry

    comment_match = COMMENT_OBJECT_RE.search((object_url or "").strip())
    if comment_match:
        comment = Comment.objects.filter(
            serial=comment_match.group("comment"),
            author__serial=comment_match.group("author"),
        ).first()
        if comment is not None:
            return "comment", comment

    return None, None


def normalize_remote_base_url(value):
    value = (value or "").strip().rstrip("/")
    if value.endswith("/api"):
        value = value[:-4]
    return value


def payload_matches_authenticated_node(author_payload, remote_node):
    author_host = normalize_remote_base_url(author_payload.get("host"))
    author_id = (author_payload.get("id") or "").strip()
    return author_host == remote_node.base_url and author_id.startswith(f"{remote_node.base_url}/")


def get_origin_author_payload(payload):
    object_type = (payload.get("type") or "").lower()
    if object_type in {"follow", "accept", "unfollow"}:
        return payload.get("actor")

    author_payload = payload.get("author")
    if isinstance(author_payload, dict):
        return author_payload
    return payload.get("actor")


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
    for field in ("host", "displayName", "github", "profileImage", "web", "description"):
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
        return None, "Entry id is required", False

    author = create_or_update_author(payload.get("author"), request)
    if author is None:
        return None, "Entry author is required", False

    entry = resolve_object_by_url(Entry, entry_id)
    created = entry is None
    if created:
        entry = Entry(author=author, url=entry_id)

    entry.author = author
    entry.url = entry_id
    entry.title = (payload.get("title") or "").strip() or "Untitled"
    entry.visibility = payload.get("visibility") if payload.get("visibility") in ("PUBLIC", "UNLISTED", "FRIENDS", "DELETED") else "PUBLIC"
    published = parse_remote_published(payload)
    if published is not None:
        entry.published = published
    incoming_web = payload.get("web")
    if incoming_web:
        entry.web = incoming_web
    elif not getattr(entry, "web", ""):
        base = normalize_url(request.build_absolute_uri("/"))
        entry.web = f"{base}/authors/{author.serial}/entries/{entry.serial}"
    
    content = payload.get("content") or ""
    content_type = payload.get("contentType", payload.get("content_type", "text/plain"))
    image_url = payload.get("imageUrl", payload.get("image_url", "")) or ""
    entry.content_type = content_type
        
    if "image" in content_type and "base64" in content_type and content:
        if content.startswith("data:"):
            try:
                content = content.split(",", 1)[1]
            except IndexError:
                pass
        
        try:
            image_data = base64.b64decode(content)
            ext = "png" if "png" in content_type.lower() else "jpg"
            
            newImage = Image(author=author)
            newImage.image.save(f"remote_{entry.serial}.{ext}", ContentFile(image_data), save=False)
            newImage.save()
            
            entry.image_url = newImage.url
            entry.content = "" 
        except Exception as e:
            print(f"Failed to decode remote base64 image: {e}")
            entry.content = content
            entry.image_url = image_url
    else:
        entry.content = content
        entry.image_url = image_url
    entry.save()
    return entry, None, created


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
    if comment is None:
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
    object_author_payload = payload.get("object") or payload.get("target")
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

    target_type, target = resolve_like_object_for_inbox(object_url)
    if target_type == "entry":
        published = parse_remote_published(payload)
        like, _ = EntryLike.objects.get_or_create(
            author=author,
            entry=target,
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

    if target_type == "comment":
        published = parse_remote_published(payload)
        like, _ = CommentLike.objects.get_or_create(
            author=author,
            comment=target,
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

    target_type, target = resolve_like_object_for_inbox(object_url)
    if target_type == "entry":
        EntryLike.objects.filter(author=author, entry=target).delete()
        return None, None

    if target_type == "comment":
        CommentLike.objects.filter(author=author, comment=target).delete()
        return None, None

    return None, "Like object target not found"


def build_item_id_from_payload(payload, request_method):
    payload_type = (payload.get("type") or "unknown").lower()
    if payload_type == "entry":
        dedup_payload = {
            "method": request_method,
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

    dedup_payload = {
        "method": request_method,
        "payload": payload,
    }
    generated = uuid.uuid5(
        uuid.NAMESPACE_URL,
        json.dumps(dedup_payload, sort_keys=True, separators=(",", ":"), default=str),
    )
    return f"https://inbox.local/events/{payload_type}/{generated}"


@api_view(["POST", "PUT", "DELETE"])
@authentication_classes([SessionAuthentication])
def inbox_item(request, author_serial):
    """Remote inbox endpoint for federated activity delivery.
    """
    inbox_owner = get_object_or_404(Author, serial=author_serial)

    auth_response = require_remote_node_auth(request)
    if auth_response is not None:
        return auth_response

    payload = request.data if isinstance(request.data, dict) else {}
    object_type = (payload.get("type") or "").lower()
    if object_type not in {"entry", "follow", "like", "comment", "accept", "unfollow", "unlike"}:
        return Response({"error": "Unsupported inbox object type"}, status=400)

    origin_author = get_origin_author_payload(payload)
    if not isinstance(origin_author, dict):
        return Response({"error": "Author payload is required."}, status=400)
    if not origin_author.get("id") or not origin_author.get("host") or not origin_author.get("displayName"):
        return Response({"error": "Author payload must include id, host, and displayName."}, status=400)
    if not payload_matches_authenticated_node(origin_author, request.remote_node):
        return Response({"error": "Payload author does not match the authenticated remote node."}, status=403)

    event_id = build_item_id_from_payload(payload, request.method)
    if InboxItem.objects.filter(owner=inbox_owner, item_id=event_id).exists():
        return Response({"type": object_type, "status": "already-processed"}, status=200)

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

    if request.method == "POST":
        if object_type == "entry":
            entry, error, _ = create_or_update_entry(payload, request)
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
            response = Response({"type": "like", "id": like.url, "object": payload.get("object")}, status=201)

    elif request.method == "PUT":
        if object_type != "entry":
            return Response({"error": "Only entry objects can be edited via inbox."}, status=403)
        entry, error, created = create_or_update_entry(payload, request)
        if error:
            return Response({"error": error}, status=400)
        response = Response(build_entry_payload(entry, request), status=201 if created else 200)

    else:  # DELETE
        if object_type != "entry":
            return Response({"error": "Only entry objects can be deleted via inbox."}, status=403)
        delete_payload = {**payload, "visibility": "DELETED"}
        entry, error, _ = create_or_update_entry(delete_payload, request)
        if error:
            return Response({"error": error}, status=400)
        if entry.visibility != "DELETED":
            entry.visibility = "DELETED"
            entry.save(update_fields=["visibility"])
        response = Response(status=204)

    InboxItem.objects.create(
        owner=inbox_owner,
        item_type=object_type,
        item_id=event_id,
        payload=payload,
    )
    return response
