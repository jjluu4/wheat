from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import uuid

from ..auth import require_remote_node_auth
from ..models import Author, Entry

from ..helpers import build_entry_payload


def normalize_remote_base_url(value):
    value = (value or "").strip().rstrip("/")
    if value.endswith("/api"):
        value = value[:-4]
    return value


def payload_matches_authenticated_node(author_content, remote_node):
    author_host = normalize_remote_base_url(author_content.get("host"))
    author_id = (author_content.get("id") or "").strip()
    return author_host == remote_node.base_url and author_id.startswith(f"{remote_node.base_url}/")

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
@authentication_classes([])
@permission_classes([])
def inbox_item(request, author_serial):
    auth_response = require_remote_node_auth(request)
    if auth_response is not None:
        return auth_response

    base_host = request.get_host()
    get_object_or_404(Author, serial=author_serial)
    authorContent = request.data.get('author')
    if not isinstance(authorContent, dict):
        return Response({"error": "Author payload is required."}, status=400)

    if not authorContent.get("id") or not authorContent.get("host") or not authorContent.get("displayName"):
        return Response({"error": "Author payload must include id, host, and displayName."}, status=400)

    if not payload_matches_authenticated_node(authorContent, request.remote_node):
        return Response({"error": "Payload author does not match the authenticated remote node."}, status=403)

    try:
        entryAuthor = Author.objects.get(url=authorContent['id'])
    except Author.DoesNotExist:
        entryAuthor = create_remote_author(authorContent, base_host)
        
    
    if request.method == "POST":
        if author_serial == entryAuthor.serial:
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
            except Entry.DoesNotExist:
                entry = create_remote_entry(request, entryAuthor, base_host)
                
                return Response(build_entry_payload(entry, request), status=201)
        
        if object_type == "follow":
            pass
    
    if request.method == "DELETE":
        object_type = request.data.get("type")
        
        if object_type == "follow":
            return Response({"error": "Should not be deleting follow objects"}, status=403)
        if object_type == "like":
            return Response({"error": "Should not be deleting like objects"}, status=403)
        if object_type == "comment":
            return Response({"error": "Should not be deleting comment objects"}, status=403)        
        
        if object_type == "entry":
            try:
                entry = Entry.objects.get(url=request.data.get("id"))            
                entry.visibility = "DELETED"    
                entry.save(update_fields=["visibility"])
                return Response(build_entry_payload(entry, request), status=204)
            except Entry.DoesNotExist:
                entry = create_remote_entry(request, entryAuthor, base_host)
                entry.visibility = "DELETED"    
                entry.save(update_fields=["visibility"])
                return Response(build_entry_payload(entry, request), status=204)
