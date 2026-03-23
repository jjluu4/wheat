from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import urllib
import requests
from ..auth import (
    add_auth_headers,
    is_local_author_authenticated,
    is_remote_node_authenticated,
    require_auth_for_view,
)
from ..helpers import normalize_url
from ..models import Author, Follow, RemoteNode
from ..serializers import AuthorSerializer


def forward_follow_request_to_remote_inbox(actor, target):
    target_host = normalize_url(getattr(target, "host", ""))
    if not target_host or "testserver" in target_host:
        return

    base_url = target_host[:-4] if target_host.endswith("/api") else target_host
    remote = RemoteNode.objects.filter(base_url=base_url, is_active=True).first()
    if remote is None:
        return

    inbox_url = f"{target_host}/authors/{target.serial}/inbox"
    payload = {
        "type": "follow",
        "summary": f"{actor.displayName} wants to follow {target.displayName}",
        "actor": AuthorSerializer(actor).data,
        "object": AuthorSerializer(target).data,
    }
    headers = add_auth_headers({"Content-Type": "application/json"}, remote)
    try:
        requests.post(inbox_url, json=payload, headers=headers, timeout=5)
    except requests.RequestException:
        return

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
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
    
    followingList = author.get_following()
    serializer = AuthorSerializer(followingList, many=True)

    return Response({
        "type": "following", 
        "following": serializer.data
        })

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
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
    
    requestList = Follow.objects.filter(target=author, status="REQUESTED")

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

    followers = Author.objects.filter(following__target=author, following__status="ACCEPTED")
    serializer = AuthorSerializer(followers, many=True)
    return Response({
        "type": "followers",
        "followers": serializer.data,
    })

@api_view(['GET', 'DELETE', 'PUT'])
@authentication_classes([SessionAuthentication])
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
    
    decoded_fqid = urllib.parse.unquote(foreign_author_fqid)
    foreign_author = Author.objects.filter(url=decoded_fqid).first()
    
    if request.method == "GET":
        if not foreign_author:
            return Response({"is_following": False}, status=200)
        
        is_following = Follow.objects.filter(actor=author, target=foreign_author, status="ACCEPTED").exists()
        return Response({"is_following": is_following}, status=200)

    elif request.method == "DELETE":
        if foreign_author:
            Follow.objects.filter(actor=author, target=foreign_author).delete()
        return Response(status=204)

    elif request.method == "PUT":
        if not foreign_author:
            return Response({"error": "Foreign author not found."}, status=404)

        follow, created = Follow.objects.get_or_create(actor=author, target=foreign_author)

        if follow.status != "ACCEPTED":
            follow.status = "REQUESTED"
            follow.save()

            forward_follow_request_to_remote_inbox(author, foreign_author)

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
    
    decoded_fqid = urllib.parse.unquote(foreign_author_fqid)
    foreign_author = Author.objects.filter(url=decoded_fqid).first()

    if request.method == "GET":
        # Local owner or authenticated remote node may check follower status.
        if not (is_local_author_authenticated(request, author) or is_remote_node_authenticated(request)):
            return Response(data="Authentication is required.", status=401)
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
        if foreign_author:
            Follow.objects.filter(actor=foreign_author, target=author).delete()
        return Response(status=204)

    elif request.method == "PUT":
        if not is_local_author_authenticated(request, author):
            if not request.user.is_authenticated:
                return Response(data="Authentication is required.", status=401)
            return Response(data="You don't have permission to manage these followers.", status=403)
        if not foreign_author:
            return Response({"error": "Foreign author not found."}, status=404)

        follow, created = Follow.objects.get_or_create(actor=foreign_author, target=author)

        if follow.status == "REQUESTED" or created:
            follow.status = "ACCEPTED"
            follow.save()
            return Response(status=204)
        else:
            return Response({"error": "There was an error processing your request."}, status=400)