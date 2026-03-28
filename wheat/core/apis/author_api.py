from django.db.models import Q
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import urllib

from ..auth import is_remote_node_authenticated, require_auth_for_view
from ..models import Author, RemoteNode
from ..serializers import AuthorSerializer
from ..helpers import fetch_remote_authors_page, fetch_remote_resource, get_pagination_params


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
def all_authors(request):
    """
    Paginated authors known to this node: registered users (active) plus federated
    authors stored locally (e.g. from inbox). Remote nodes are listed separately via
    GET /api/remote-nodes/<pk>/authors/ when a client wants that node's catalog.
    """
    require_auth_for_view(False)
    page, size = get_pagination_params(request)
    offset = (page - 1) * size

    authors_qs = (
        Author.objects.filter(
            Q(user__isnull=True) | Q(user__isnull=False, user__is_active=True)
        )
        .order_by("displayName", "serial")
    )
    total = authors_qs.count()
    page_rows = authors_qs[offset : offset + size]

    serializer = AuthorSerializer(page_rows, many=True, context={"request": request})

    return Response(
        {
            "type": "authors",
            "authors": serializer.data,
            "page_number": page,
            "size": size,
            "count": total,
        }
    )


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def remote_node_authors(request, remote_node_pk):
    """
    Proxy one paginated GET to a configured remote node's /api/authors.
    Upserts returned authors locally (entries are still inbox-only).
    Requires a logged-in user so anonymous clients cannot abuse node credentials.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)

    node = get_object_or_404(RemoteNode, pk=remote_node_pk, is_active=True)
    page, size = get_pagination_params(request)
    result = fetch_remote_authors_page(node, page, size)
    if result["error"]:
        return Response({"error": result["error"]}, status=502)

    serializer = AuthorSerializer(result["authors"], many=True, context={"request": request})
    return Response(
        {
            "type": "authors",
            "authors": serializer.data,
            "page_number": page,
            "size": size,
            "has_more": result["has_more"],
        }
    )

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
