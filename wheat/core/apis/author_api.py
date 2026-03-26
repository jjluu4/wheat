from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import urllib

from ..auth import is_remote_node_authenticated, require_auth_for_view
from ..models import Author
from ..serializers import AuthorSerializer
from ..helpers import fetch_remote_resource, get_pagination_params


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
def all_authors(request):
    """
    Retrieves a paginated list of all authors on this node

    parameters:
        - page: Page number (default: 1)
        - size: Number of authors per page (default: 5)
    """
    require_auth_for_view(False)
    page, size = get_pagination_params(request)
    offset = (page - 1) * size

    authors = Author.objects.all().order_by("url")
    
    serializer = AuthorSerializer(authors[offset:offset + size], many=True)
    
    return Response({
        "type": "authors", 
        "authors": serializer.data,
    })

@api_view(['GET', 'PUT'])
@authentication_classes([SessionAuthentication])
def single_author(request, author_serial):
    """
    Handles operations on a single author profile

    GET: Retrieve the author's profile information
    PUT: Update the author's profile. Requires authentication as the author
    """
    author = get_object_or_404(Author, serial=author_serial)

    if request.method == 'GET':
        require_auth_for_view(False)
        serializer = AuthorSerializer(author)
        return Response(serializer.data)

    require_auth_for_view(True)
    if not request.user.is_authenticated:
        return Response(data={"error": "Authentication required to update profile"}, status=401)

    if not hasattr(request.user, 'author_profile') or request.user.author_profile != author:
        return Response(data={"error": "You don't have permission to update this profile"}, status=403)

    for field in ['displayName', 'github', 'profileImage']:
        if field in request.data:
            setattr(author, field, request.data[field])

    author.save()
    serializer = AuthorSerializer(author)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
def single_author_fqid(request, author_fqid):
    """
    Retrieves an author's profile information by fqid.

    GET: Retrieve the author's profile information.
    """
    require_auth_for_view(False)
    if not (request.user.is_authenticated or is_remote_node_authenticated(request)):
        return Response({"error": "Authentication required"}, status=401)

    decoded_fqid = urllib.parse.unquote(author_fqid)
    try:
        author = Author.objects.get(url=decoded_fqid)
        return Response(AuthorSerializer(author).data)
    except Author.DoesNotExist:
        return fetch_remote_resource(decoded_fqid)