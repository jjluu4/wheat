from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..auth import require_auth_for_view
from ..models import Author, Follow
from ..serializers import AuthorSerializer

@api_view(['GET'])
def get_following_api(request, author_serial):
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