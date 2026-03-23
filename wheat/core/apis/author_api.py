import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import urllib

from ..auth import require_auth_for_view, add_auth_headers
from ..models import Author, RemoteNode
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

    try:
        author = get_object_or_404(Author, url=decoded_fqid)
        return Response(AuthorSerializer(author).data)
    except:
        ...

    if not decoded_fqid.startswith(('http://', 'https://')):
        decoded_fqid = 'http://' + decoded_fqid

    parsed_url = urllib.parse.urlparse(decoded_fqid)
    if not parsed_url.netloc:
        return Response({"error": "Invalid author FQID format"},status=400)

    remote_host = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    try:
        remote_node = RemoteNode.objects.get(base_url=remote_host, is_active=True)

        headers = {'Accept': 'application/json','User-Agent': 'SocialDistribution/1.0'}
        headers = add_auth_headers(headers, remote_node)

        response = requests.get(
            decoded_fqid,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return Response(response.json())
        elif response.status_code == 404:
            return Response({"error": "Author not found on remote node"}, status=404)
        else:
            return Response({"error": f"Remote node returned status {response.status_code}"},status=502)

    except RemoteNode.DoesNotExist:
        return Response({"error": "Remote node not configured or inactive"},status=400)

    except requests.exceptions.RequestException as e:
        return Response({"error": f"Failed to connect to remote node: {str(e)}"},status=503)