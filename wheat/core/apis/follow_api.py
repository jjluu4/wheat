from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import urllib

from ..auth import require_auth_for_view
from ..models import Author, Follow
from ..serializers import AuthorSerializer

@api_view(['GET'])
def get_following_list(request, author_serial):
    """
    Retrieves the list of authors that the specified author is following
    
    Requires authentication as the author
    """
    require_auth_for_view(True)
    author = get_object_or_404(Author, serial=author_serial)

    if not request.user.is_authenticated:
        return Response(data="Authentication is required to retrieve the following list.", status=401)
    
    if author.user != request.user:
        return Response(data="You don't have permission to view this following list.", status=403)
    
    followingList = author.get_following()
    serializer = AuthorSerializer(followingList, many=True)

    return Response({
        "type": "following", 
        "following": serializer.data
        })

@api_view(['GET'])
def get_follow_requests_api(request, author_serial):
    """
    Retrieves all pending follow requests for the specified author, returns a list of follow request objects

    Requires authentication as the author
    """
    require_auth_for_view(True)
    author = get_object_or_404(Author, serial=author_serial)

    if not request.user.is_authenticated:
        return Response(data="Authentication is required to retrieve these follow requests.", status=401)
    
    if author.user != request.user:
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

@api_view(['GET', 'DELETE', 'PUT'])
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
    if author.user != request.user:
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

            serializedActor = AuthorSerializer(author)
            serializedTarget = AuthorSerializer(foreign_author)

            payload = {
                "type": "follow",
                "summary": f"{author.displayName} wants to follow {foreign_author.displayName}",
                "actor": serializedActor.data,
                "target": serializedTarget.data,
            }
        
        # TODO: A follow request should be sent to the target's inbox API.
        
        return Response(status=204)

@api_view(['GET', 'DELETE', 'PUT'])
def follower_api(request, author_serial, foreign_author_fqid):
    """
    Handles operations to manage a single follower relationship.

    GET: Checks if the author is followed by a foreign author.
    DELETE: Removes a foreign author as a follower.
    PUT: Accepts a follow request from a foreign author.
    """
    require_auth_for_view(True)
    if not request.user.is_authenticated:
        return Response(data="Authentication is required.", status=401)
    
    author = get_object_or_404(Author, serial=author_serial)
    if author.user != request.user:
        return Response(data="You don't have permission to manage these followers.", status=403)
    
    decoded_fqid = urllib.parse.unquote(foreign_author_fqid)
    foreign_author = Author.objects.filter(url=decoded_fqid).first()
    
    if request.method == "GET":
        if not foreign_author:
            return Response({"is_follower": False}, status=200)
        
        is_follower = Follow.objects.filter(actor=foreign_author, target=author, status="ACCEPTED").exists()
        return Response({"is_follower": is_follower}, status=200)

    elif request.method == "DELETE":
        if foreign_author:
            Follow.objects.filter(actor=foreign_author, target=author).delete()
        return Response(status=204)

    elif request.method == "PUT":
        if not foreign_author:
            return Response({"error": "Foreign author not found."}, status=404)

        follow, created = Follow.objects.get_or_create(actor=foreign_author, target=author)

        if follow.status == "REQUESTED" or created:
            follow.status = "ACCEPTED"
            follow.save()
            return Response(status=204)
        else:
            return Response({"error": "There was an error processing your request."}, status=400)