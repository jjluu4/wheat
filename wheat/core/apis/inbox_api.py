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

def create_remote_author(authorContent, base_host):
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
    return entryAuthor

def create_remote_entry(request, entryAuthor, base_host):
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
    return entry
    
@api_view(["POST", "PUT", "DELETE"])
def inbox_item(request, author_serial):
    base_host = request.get_host()
    authorContent = request.data.get('author')
    base_url_match = authorContent["host"].replace("/api/", "")
    matchRemoteNode = RemoteNode.objects.filter(is_active=True, base_url=base_url_match)
    
    if len(matchRemoteNode) == 0:
        return Response({"NO CONTENT": "Post was not created. Foreign node is not active on this node."}, status=204)
    
    try:
        entryAuthor = Author.objects.get(url=authorContent['id'])
    except:
        entryAuthor = create_remote_author(authorContent, base_host)
        
    
    if request.method == "POST":
        require_auth_for_view(True)

        if not author_serial!=entryAuthor.serial:
            return Response(data={"error": "You don't have permission to post entries for this author."},status=403)
        
        object_type = request.data.get("type")
        
        if object_type == "entry":
            
            newEntry = create_remote_entry(request, entryAuthor, base_host)
            
            return Response(build_entry_payload(newEntry, request), status=201)
        
        elif object_type == "follow":
            pass
        elif object_type == "like":
            pass
        elif object_type == "comment":
            pass
    
    if request.method == "PUT":
        #require_auth_for_view(True)
        
        object_type = request.data.get("type")
        
        if object_type == "like":
            return Response({"error": "Should not be editing like objects"}, status=403)
        if object_type == "comment":
            return Response({"error": "Should not be editing comment objects"}, status=403)       
        
        if object_type == "entry":
            
            try:
                entry = Entry.objects.get(url=request.data.get("id"))
                if "title" in request.data:
                    entry.title = (request.data.get("title") or "").strip() or entry.title
                if "content" in request.data:
                    entry.content = request.data["content"]
                if "contentType" in request.data:
                    entry.content_type = request.data["contentType"]
                if "content_type" in request.data:
                    entry.content_type = request.data["content_type"]
                if "imageUrl" in request.data:
                    entry.image_url = request.data["imageUrl"]
                if "image_url" in request.data:
                    entry.image_url = request.data["image_url"]
                if "visibility" in request.data and request.data["visibility"] in ("PUBLIC", "UNLISTED", "FRIENDS"):
                    entry.visibility = request.data["visibility"]
                

                if entry.content_type == "image" and not entry.image_url:
                    return Response({"error": "imageUrl is required for image entries"}, status=400)

                entry.save()
                return Response(build_entry_payload(entry, request), status=200)                
            except:
                entry = create_remote_entry(request, entryAuthor, base_host)
                
                return Response(build_entry_payload(entry, request), status=201)
        
        if object_type == "follow":
            pass
    
    if request.method == "DELETE":
        require_auth_for_view(True)
        
        object_type = request.data.get("type")
        
        if object_type == "follow":
            return Response({"error": "Should not be deleting follow objects"}, status=403)
        if object_type == "like":
            return Response({"error": "Should not be deleting like objects"}, status=403)
        if object_type == "comment":
            return Response({"error": "Should not be deleting comment objects"}, status=403)        
        
        if object_type == "entry":
            
            require_auth_for_view(True)
            try:
                entry = Entry.objects.get(url=request.data.get("id"))            
                entry.visibility = "DELETED"    
                entry.save(update_fields=["visibility"])
                return Response(build_entry_payload(entry, request), status=204)
            except:
                entry = create_remote_entry(request, entryAuthor, base_host)
                entry.visibility = "DELETED"    
                entry.save(update_fields=["visibility"])
                return Response(build_entry_payload(entry, request), status=204)