from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import urllib

from ..auth import require_auth_for_view
from ..models import Author
from ..serializers import AuthorSerializer

@api_view(['GET'])
def all_authors(request):
    """
    Retrieves a paginated list of all authors on this node

    parameters:
        - page: Page number (default: 1)
        - size: Number of authors per page (default: 5)
    """
    require_auth_for_view(False)

    try:
        page=int(request.GET.get('page', 1))
        if page < 1:
            page=1
    except:
        page=1

    try:
        size=int(request.GET.get('size', 5))
        if size < 1:
            size=5
    except:
        size=5

    offset=(page-1)*size

    serializer=AuthorSerializer(Author.objects.all()[offset:offset+size], many=True)

    return Response({"type": "authors", "authors": serializer.data})

@api_view(['GET', 'PUT'])
def single_author(request, author_serial): 
    """
    Handles operations on a single author profile

    GET: Retrieve the author's profile information
    PUT: Update the author's profile. Requires authentication as the author
    """
    author=get_object_or_404(Author, serial=author_serial)

    if request.method=='GET':
        require_auth_for_view(False)
        serializer=AuthorSerializer(author)
        return Response(serializer.data)

    elif request.method=='PUT':
        require_auth_for_view(True)
        if not request.user.is_authenticated:
            return Response(data={"error": "Authentication required to update profile"},status=401)

        if not hasattr(request.user,'author_profile') or request.user.author_profile!=author:
            return Response(data={"error": "You don't have permission to update this profile"},status=403)

        for field in ['displayName', 'github', 'profileImage']:
            if field in request.data:
                setattr(author, field, request.data[field])

        author.save()

        serializer=AuthorSerializer(author)
        return Response(serializer.data)

@api_view(['GET'])
def single_author_fqid(request, author_fqid): 
    """
    Retrieves an author's profile information by fqid.

    GET: Retrieve the author's profile information.
    """
    require_auth_for_view(False)

    decoded_fqid = urllib.parse.unquote(author_fqid)
    author = get_object_or_404(Author, url=decoded_fqid)
    return Response(AuthorSerializer(author).data)