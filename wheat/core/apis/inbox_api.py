from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import uuid

from ..auth import require_auth_for_view
from ..models import Author, Entry, RemoteNode
from ..permissions import (
    get_requesting_author,
    can_view_entry,
)

from ..helpers import get_pagination_params, build_entry_payload
from ..serializers import AuthorSerializer
    
@api_view(["POST"])
def inbox_item(request, author_serial):
    base_host = request.get_host()
    authorContent = request.data.get('author')
    base_url_match = authorContent["host"].replace("/api/", "")
    matchRemoteNode = RemoteNode.objects.filter(is_active=True, base_url=base_url_match)
    
    if len(matchRemoteNode) == 0:
        return Response({"NO CONTENT": "Post was not created as foreign node is not active on this node."}, status=204)
    
    try:
        entryAuthor = Author.objects.get(url=authorContent['id'])
    except:
        
        authorSerial = uuid.uuid4()
        entryAuthor = Author.objects.create(
            displayName = authorContent["displayName"],
            serial = authorSerial
        )        
        
        for field in ['github', 'profileImage', 'description', 'host']:
            if field in authorContent.keys():
                setattr(entryAuthor, field, authorContent[field])
        
        entryAuthor.url = authorContent['id']
        entryAuthor.web = f"{base_host}/authors/{entryAuthor.serial}"
        entryAuthor.save()
    
    if request.method == "POST":
        require_auth_for_view(True)
        
        object_type = request.data.get("type")
        
        if object_type == "entry":
            
            content = request.data.get("content", "")
            content_type = request.data.get("contentType", request.data.get("content_type", "text/plain"))
            image_url = request.data.get("imageUrl", request.data.get("image_url", ""))
            title = (request.data.get("title") or "").strip() or "Untitled"
            visibility = request.data.get("visibility", "PUBLIC")
            if visibility not in ("PUBLIC", "UNLISTED", "FRIENDS"):
                visibility = "PUBLIC"

            if content_type == "image" and not image_url:
                return Response({"error": "imageUrl is required for image entries"}, status=400)

            entry = Entry.objects.create(
                    author=entryAuthor,
                    url="",
                    title=title,
                    content=content,
                    content_type=content_type,
                    image_url=image_url,
                    visibility=visibility,
            )
            
            entry.url = request.data.get("id", "")
            entry.web = f"{base_host}/authors/{entryAuthor.serial}/entries/{entry.serial}"
            entry.save()
            
            return Response(build_entry_payload(entry, request), status=201)
        
        elif object_type == "follow":
            pass
        elif object_type == "like":
            pass
        elif object_type == "comment":
            pass