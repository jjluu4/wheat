from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import urllib
import uuid
import logging
from ..auth import (
    add_auth_headers,
    is_local_author_authenticated,
    is_remote_node_authenticated,
    require_auth_for_view,
)
from ..helpers import (
    author_requires_remote_inbox,
    decode_fqid,
    get_pagination_params,
    normalize_url,
    resolve_object_by_url,
    resolve_remote_author,
    send_json_to_remote_author_inbox,
)
from ..models import Author, Follow
from ..serializers import AuthorSerializer

logger = logging.getLogger(__name__)


def _extract_author_id_from_fqid(author_fqid):
    """
    Extract the author id segment from a remote author FQID.
    Example: https://node/api/authors/<id> -> <id>
    """
    path_parts = [part for part in urllib.parse.urlparse(author_fqid).path.split("/") if part]
    for idx, part in enumerate(path_parts):
        if part == "authors" and idx + 1 < len(path_parts):
            return path_parts[idx + 1]
    return None


def _contextualize_remote_inbox_error(error, action_name):
    """Rewrite shared inbox helper errors with action-specific wording."""
    if not error:
        return error
    if "rejected request with status" in error:
        return error.replace("rejected request", f"rejected {action_name}")
    if error.startswith("Failed to reach remote inbox:"):
        return error.replace(
            "Failed to reach remote inbox:",
            f"Failed to reach remote inbox for {action_name}:",
            1,
        )
    return error


def notify_remote_follow_event(
    *,
    remote_recipient,
    event_type,
    event_id,
    summary,
    actor,
    obj,
    error_action_name,
    timeout=5,
):
    """
    helper for handling follow related events
    """
    if not author_requires_remote_inbox(remote_recipient):
        return True, None
    recipient_fqid = normalize_url(getattr(remote_recipient, "url", ""))

    payload = {
        "type": event_type,
        "id": event_id,
        "summary": summary,
        "actor": AuthorSerializer(actor).data,
        "object": AuthorSerializer(obj).data,
    }
    delivered, error = send_json_to_remote_author_inbox(recipient_fqid, payload, timeout=timeout)
    if delivered:
        return True, None
    return False, _contextualize_remote_inbox_error(error, error_action_name)

def forward_follow_request_to_remote_inbox(actor, target):
    """
    deliver a follow request to the target authors remote inbox
    """
    follow_event_id = f"{normalize_url(actor.url)}/follows/{uuid.uuid4()}"
    return notify_remote_follow_event(
        remote_recipient=target,
        event_type="follow",
        event_id=follow_event_id,
        summary=f"{actor.displayName} wants to follow {target.displayName}",
        actor=actor,
        obj=target,
        error_action_name="follow request",
        timeout=5,
    )


def notify_remote_follow_acceptance(remote_follower, local_followed_author):
    """
    notify the remote follower's node that the follow request was accepted
    """
    accept_event_id = f"{normalize_url(local_followed_author.url)}/accepts/{uuid.uuid4()}"
    return notify_remote_follow_event(
        remote_recipient=remote_follower,
        event_type="accept",
        event_id=accept_event_id,
        summary=f"{local_followed_author.displayName} accepted your follow request",
        actor=local_followed_author,
        obj=remote_follower,
        error_action_name="accept",
        timeout=5,
    )


def notify_remote_unfollow(actor, target):
    """
    tell the followee's node to remove Follow(actor=actor, target=target) so followers/following stay in sync
    """
    unfollow_event_id = f"{normalize_url(actor.url)}/unfollows/{uuid.uuid4()}"
    return notify_remote_follow_event(
        remote_recipient=target,
        event_type="unfollow",
        event_id=unfollow_event_id,
        summary=f"{actor.displayName} unfollowed {target.displayName}",
        actor=actor,
        obj=target,
        error_action_name="unfollow",
        timeout=5,
    )


def notify_remote_follow_removed_by_followee(follower, followee):
    """
    When the followee removes a follower, notify the follower's home node to delete Follow(follower, followee).
    """
    unfollow_event_id = f"{normalize_url(followee.url)}/unfollows/{uuid.uuid4()}"
    return notify_remote_follow_event(
        remote_recipient=follower,
        event_type="unfollow",
        event_id=unfollow_event_id,
        summary=f"{followee.displayName} removed {follower.displayName} as a follower",
        actor=follower,
        obj=followee,
        error_action_name="unfollow",
        timeout=5,
    )


def notify_remote_follow_rejection(remote_follower, local_followed_author):
    """
    When the followee rejects a pending request, notify the follower's node to drop Follow(follower, followee).
    Same inbox shape as remove-follower / unfollow.
    """
    return notify_remote_follow_removed_by_followee(remote_follower, local_followed_author)


@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def get_following_list(request, author_serial):
    """
    Retrieves the list of authors that the specified author is following
    
    Requires authentication as the author
    """
    require_auth_for_view(True)
    author = get_object_or_404(Author, serial=author_serial)

    if not request.user.is_authenticated:
        return Response(data="Authentication is required to retrieve the following list.", status=401)

    if not is_local_author_authenticated(request, author):
        return Response(data="You don't have permission to view this following list.", status=403)
    
    page, size = get_pagination_params(request)
    offset = (page - 1) * size
    following_query = Author.objects.filter(
        followers__actor=author,
        followers__status__in=["REQUESTED", "ACCEPTED"],
    ).order_by("displayName", "url").distinct()
    total = following_query.count()
    serializer = AuthorSerializer(following_query[offset:offset + size], many=True)

    return Response({
        "type": "following", 
        "page_number": page,
        "size": size,
        "count": total,
        "following": serializer.data
        })

@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def get_follow_requests_api(request, author_serial):
    """
    Retrieves all pending follow requests for the specified author, returns a list of follow request objects

    Requires authentication as the author
    """
    require_auth_for_view(True)
    author = get_object_or_404(Author, serial=author_serial)

    if not request.user.is_authenticated:
        return Response(data="Authentication is required to retrieve these follow requests.", status=401)

    if not is_local_author_authenticated(request, author):
        return Response(data="You don't have permission to view these follow requests.", status=403)
    
    page, size = get_pagination_params(request)
    offset = (page - 1) * size
    requestList = Follow.objects.filter(target=author, status="REQUESTED").select_related("actor").order_by(
        "actor__displayName", "actor__url"
    )[offset:offset + size]

    serializedAuthor = AuthorSerializer(author).data

    data = []
    for request in requestList:
        serializedActor = AuthorSerializer(request.actor).data
        data.append({
            "type": "follow",
            "summary": f"{request.actor} wants to follow {request.target}",
            "actor": serializedActor,
            "object": serializedAuthor
        })

    return Response(data)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
def followers_api(request, author_serial):
    """
    GET followers collection for an author.
    """
    author = get_object_or_404(Author, serial=author_serial)
    require_auth_for_view(True)

    if not (is_local_author_authenticated(request, author) or is_remote_node_authenticated(request)):
        return Response(data="Authentication is required.", status=401)

    page, size = get_pagination_params(request)
    offset = (page - 1) * size
    followers_query = Author.objects.filter(
        following__target=author,
        following__status="ACCEPTED",
    ).order_by("displayName", "url").distinct()
    total = followers_query.count()
    serializer = AuthorSerializer(followers_query[offset:offset + size], many=True)
    return Response({
        "type": "followers",
        "page_number": page,
        "size": size,
        "count": total,
        "followers": serializer.data,
    })

@api_view(['GET', 'DELETE', 'PUT'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def following_api(request, author_serial, foreign_author_fqid):
    """
    Handles operations to manage a single following relationship.

    GET: Checks if the author is following a foreign author.
    DELETE: Unfollows a foreign author.
    PUT: Generates a follow request to a foreign author.
    """
    require_auth_for_view(True)
    if not request.user.is_authenticated:
        return Response(data="Authentication is required.", status=401)
    
    author = get_object_or_404(Author, serial=author_serial)
    if not is_local_author_authenticated(request, author):
        return Response(data="You don't have permission to manage this following list.", status=403)
    
    decoded_fqid = decode_fqid(foreign_author_fqid)
    foreign_author = resolve_object_by_url(Author, decoded_fqid)
    
    if request.method == "GET":
        if not foreign_author:
            return Response({"is_following": False}, status=200)
        
        is_following = Follow.objects.filter(
            actor=author,
            target=foreign_author,
            status__in=["REQUESTED", "ACCEPTED"],
        ).exists()
        return Response({"is_following": is_following}, status=200)

    elif request.method == "DELETE":
        if foreign_author:
            Follow.objects.filter(actor=author, target=foreign_author).delete()
            delivered, err = notify_remote_unfollow(author, foreign_author)
            
        return Response(status=204)

    elif request.method == "PUT":
        foreign_author = resolve_remote_author(decoded_fqid)
        if not foreign_author:
            return Response({"error": "Foreign author not found."}, status=404)
        if foreign_author.pk == author.pk or normalize_url(decoded_fqid) == normalize_url(author.url):
            return Response({"error": "Authors cannot follow themselves."}, status=400)

        follow = Follow.objects.filter(actor=author, target=foreign_author).first()
        if follow and follow.status == "ACCEPTED":
            return Response(status=204)

        if author_requires_remote_inbox(foreign_author):
            delivered, delivery_error = forward_follow_request_to_remote_inbox(author, foreign_author)
            if not delivered:
                return Response({"error": delivery_error}, status=502)

        if follow is None:
            Follow.objects.create(actor=author, target=foreign_author, status="REQUESTED")
        elif follow.status != "REQUESTED":
            follow.status = "REQUESTED"
            follow.save(update_fields=["status"])

        return Response(status=204)

@api_view(['GET', 'DELETE', 'PUT'])
@authentication_classes([SessionAuthentication])
def follower_api(request, author_serial, foreign_author_fqid):
    """
    Handles operations to manage a single follower relationship.

    GET: Checks if the author is followed by a foreign author.
    DELETE: Removes a foreign author as a follower.
    PUT: Accepts a follow request from a foreign author.
    """
    author = get_object_or_404(Author, serial=author_serial)
    require_auth_for_view(True)
    
    decoded_fqid = decode_fqid(foreign_author_fqid)
    foreign_author = resolve_object_by_url(Author, decoded_fqid)

    if request.method == "GET":
        local_author_authenticated = is_local_author_authenticated(request, author)
        remote_node_authenticated = is_remote_node_authenticated(request)
        if not (local_author_authenticated or remote_node_authenticated):
            if not request.user.is_authenticated:
                return Response(data="Authentication is required.", status=401)
            return Response(data="You don't have permission to view these followers.", status=403)

        if not foreign_author:
            return Response({"error": "Follower not found"}, status=404)

        is_follower = Follow.objects.filter(actor=foreign_author, target=author, status="ACCEPTED").exists()
        if not is_follower:
            return Response({"error": "Follower not found"}, status=404)
        return Response(AuthorSerializer(foreign_author).data, status=200)

    elif request.method == "DELETE":
        if not is_local_author_authenticated(request, author):
            if not request.user.is_authenticated:
                return Response(data="Authentication is required.", status=401)
            return Response(data="You don't have permission to manage these followers.", status=403)
        if not foreign_author:
            return Response({"error": "Follower not found"}, status=404)

        follow = Follow.objects.filter(
            actor=foreign_author,
            target=author,
            status__in=["REQUESTED", "ACCEPTED"],
        ).first()
        if follow is None:
            return Response({"error": "Follower not found"}, status=404)

        follow.delete()
        if getattr(foreign_author, "url", "") or getattr(foreign_author, "host", ""):
            delivered, err = notify_remote_follow_removed_by_followee(foreign_author, author)
            
        return Response(status=204)

    elif request.method == "PUT":
        local_ok = is_local_author_authenticated(request, author)
        remote_ok = is_remote_node_authenticated(request)
        if not (local_ok or remote_ok):
            if not request.user.is_authenticated:
                return Response(data="Authentication is required.", status=401)
            return Response(data="You don't have permission to manage these followers.", status=403)

        foreign_author = resolve_remote_author(decoded_fqid)
        if not foreign_author:
            return Response({"error": "Foreign author not found."}, status=404)

        if local_ok:
            follow = Follow.objects.filter(
                actor=foreign_author,
                target=author,
                status="REQUESTED",
            ).first()
            if follow is None:
                return Response({"error": "Follow request not found."}, status=404)

            follow.status = "ACCEPTED"
            follow.save(update_fields=["status"])
            if author_requires_remote_inbox(foreign_author):
                delivered, delivery_error = notify_remote_follow_acceptance(foreign_author, author)
                if not delivered:
                    return Response({"error": delivery_error}, status=502)
            return Response(status=204)

        follow, created = Follow.objects.get_or_create(
            actor=foreign_author,
            target=author,
            defaults={"status": "ACCEPTED"},
        )
        if not created and follow.status != "ACCEPTED":
            follow.status = "ACCEPTED"
            follow.save(update_fields=["status"])
        return Response(status=204)
