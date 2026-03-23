from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import uuid
import re

from ..auth import require_auth_for_view
from ..models import Author, Entry, Comment

from ..permissions import (
    get_requesting_author,
    can_view_entry,
    can_view_comment,
    filter_comments_for_viewer,
)

from ..helpers import (
    get_pagination_params,
    build_comment_payload,
    build_author_api_url,
    build_author_commented_collection_id,
    build_author_commented_collection_web,
    build_entry_comments_collection_id,
    build_entry_web_url,
    resolve_object_by_url,
)

@api_view(['GET', 'POST'])
def author_commented(request, author_serial):
    """
    Handles operations on an authors comments

    GET: Retrieve paginated list of comments made by the author
    POST: Create a new comment as the author. Requires authentication and the comment must be associated with a valid entry URL
    """
    author=get_object_or_404(Author, serial=author_serial)

    if request.method=='GET':
        require_auth_for_view(False)
        page, size = get_pagination_params(request)
        offset=(page - 1) * size
        requestingAuthor = get_requesting_author(request)

        comments = [
            comment
            for comment in Comment.objects.filter(author=author).select_related('author', 'entry', 'entry__author').order_by('-published')
            if can_view_comment(comment, requestingAuthor, request.user)
        ]

        total = len(comments)
        page_comments = comments[offset:offset+size]
        data = [build_comment_payload(comment, request) for comment in page_comments]

        return Response({ 
            "type": "comments",
            "id": build_author_commented_collection_id(author, request),
            "web": build_author_commented_collection_web(author, request),
            "page_number": page,
            "size": size,
            "count": total,
            "src": data,
        })

    elif request.method=='POST':
        require_auth_for_view(True)

        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        requestingAuthor=None
        if hasattr(request.user, 'author_profile'):
            requestingAuthor=request.user.author_profile

        if not requestingAuthor or requestingAuthor.serial!=author_serial:
            return Response({"error": "Cannot post as another author"}, status=403)

        data=request.data if request.content_type=='application/json' else request.POST.dict()

        if data.get('type')!='comment' and data.get('type') is not None:
            return Response({"error": "Type must be 'comment'"}, status=400)

        comment_text=data.get('comment', data.get('content'))
        if not comment_text:
            return Response({"error": "Comment text is required"}, status=400)

        entry_url=data.get('entry')
        if not entry_url:
            return Response({"error": "Entry URL is required"}, status=400)

        entry = resolve_object_by_url(Entry, entry_url)
        if entry is None:
            try:
                match=re.search(r'/authors/([^/]+)/entries/([^/]+)', entry_url)
                if not match:
                    return Response({"error": "Invalid entry URL format"}, status=400)

                entry=get_object_or_404(Entry, serial=match.groups()[1], author__serial=match.groups()[0])
            except Exception:
                return Response({"error": f"Invalid entry URL"}, status=400)

        if not can_view_entry(entry, requestingAuthor, request.user):
            return Response({"error": "You don't have permission to comment on this entry"}, status=403)

        comment_serial=uuid.uuid4()
        comment=Comment.objects.create(
            url=f"{build_author_api_url(author, request)}/commented/{comment_serial}/",
            serial=comment_serial,
            author=author,
            entry=entry,
            content_type=data.get('contentType', data.get('content_type', 'text/plain')),
            content=comment_text
        )

        # TODO: forwarding

        return Response(build_comment_payload(comment, request), status=201)

@api_view(['GET'])
def author_commented_single(request, author_serial, comment_serial):
    """
    Retrieves a specific comment made by an author

    Depends on post visibility (PUBLIC/UNLISTED viewable by anyone, FRIENDS viewable by friends, otherwise requires authentication as author)
    """
    require_auth_for_view(False) #handles manually

    author=get_object_or_404(Author, serial=author_serial)
    comment=get_object_or_404(Comment, serial=comment_serial, author=author)

    entry=comment.entry

    requesting_author = get_requesting_author(request)

    if not can_view_comment(comment, requesting_author, request.user):
        return Response({"error": "You don't have permission to view this comment"}, status=403)

    return Response(build_comment_payload(comment, request))

@api_view(['GET'])
def entry_comments(request, author_serial, entry_serial):
    """
    Retrieves paginated comments for a specific entry

    Depends on post visibility (PUBLIC/UNLISTED viewable by anyone, FRIENDS viewable by friends, otherwise requires authentication as author)
    """
    require_auth_for_view(False) #handles manually

    entry=get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    entry_author=entry.author

    requesting_author = get_requesting_author(request)
    visible_comments = filter_comments_for_viewer(
        Comment.objects.filter(entry=entry).select_related('author', 'entry__author').order_by('-published'),
        entry,
        requesting_author,
        request.user,
    )

    if not can_view_entry(entry, requesting_author, request.user) and not visible_comments.exists():
        return Response({"error": "You don't have permission to view comments on this entry"}, status=403)

    page, size = get_pagination_params(request)
    offset=(page - 1) * size
    comments = list(visible_comments[offset:offset+size])

    data=[]
    for comment in comments:
        data.append(build_comment_payload(comment, request))

    return Response({
        "type": "comments",
        "id": build_entry_comments_collection_id(entry, request),
        "web": build_entry_web_url(entry, request),
        "page_number": page,
        "size": size,
        "count": visible_comments.count(),
        "src": data,
    })
