from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import base64, urllib, mimetypes, io
from PIL import Image as PILImage

from ..auth import require_auth_for_view
from ..models import Author, Entry, Image
from ..permissions import (
    get_requesting_author,
    can_view_entry,
)
from ..helpers import get_pagination_params, build_entry_payload
from ..serializers import EntrySerializer

@api_view(["GET", "PUT", "DELETE"])
def single_entry(request, author_serial, entry_serial):
    """
    Handles operations on a single entry.
    """
    entryAuthor = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=entryAuthor)
    requestingAuthor = get_requesting_author(request)

    if request.method == "GET":
        require_auth_for_view(False)
        if not can_view_entry(entry, requestingAuthor, request.user):
            if entry.visibility == "DELETED":
                return Response({"error": "Entry not found"}, status=404)

            if not request.user.is_authenticated and entry.visibility == "FRIENDS":
                return Response({"error": "Authentication required"}, status=401)

            return Response({"error": "You don't have permission to view this entry"}, status=403)

        return Response(build_entry_payload(entry, request), status=200)

    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)

    if not hasattr(request.user, "author_profile") or request.user.author_profile != entryAuthor:
        return Response({"error": "You don't have permission to modify this entry"}, status=403)

    if request.method == "PUT":
        require_auth_for_view(True)
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

    if request.method == "DELETE":
        require_auth_for_view(True)
        entry.visibility = "DELETED"
        entry.save(update_fields=["visibility"])
        return Response(status=204)

@api_view(["GET", "POST"])
def author_entries(request, author_serial):
    """
    Handles operations on an authors entries collection

    GET: Retrieve paginated entries for an author. (PUBLIC/UNLISTED viewable by anyone, FRIENDS viewable by friends, otherwise requires authentication as author)
    POST: Create a new entry for the author. Requires authentication as the author
    """
    author = get_object_or_404(Author, serial=author_serial)

    requestingAuthor = None
    if request.user.is_authenticated and hasattr(request.user, "author_profile"):
        requestingAuthor = request.user.author_profile

    if request.method == "GET":
        require_auth_for_view(False)
        page, size = get_pagination_params(request)
        offset = (page - 1) * size

        qs = Entry.objects.filter(author=author).exclude(visibility="DELETED").order_by("-published")

        is_owner = request.user.is_authenticated and (request.user.is_staff or requestingAuthor == author)
        is_friend = requestingAuthor is not None and author.get_friends().filter(serial=requestingAuthor.serial).exists()
        is_follower = requestingAuthor is not None and author.get_followers().filter(serial=requestingAuthor.serial).exists()

        if is_owner or request.user.is_staff or is_friend:
            pass  
        elif is_follower:
            qs = qs.exclude(visibility="FRIENDS")
        else:
            qs = qs.filter(visibility="PUBLIC")

        total = qs.count()
        page_entries = list(qs[offset : offset + size])
        entryData = [build_entry_payload(entry, request) for entry in page_entries]

        return Response(
            {
                "type": "entries",
                "page_number": page,
                "size": size,
                "count": total,
                "src": entryData,
                "entries": entryData,
            }
        )

    elif request.method == "POST":
        require_auth_for_view(True)
        if not request.user.is_authenticated or not requestingAuthor:
            return Response({"error": "Authentication required to create entry"}, status=401)

        if requestingAuthor != author and not request.user.is_staff:
            return Response({"error": "You cannot add entries to another user"}, status=403)

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
            author=author,
            url="",
            title=title,
            content=content,
            content_type=content_type,
            image_url=image_url,
            visibility=visibility,
        )

        base_host = (author.host or "").rstrip("/")
        entry.url = f"{base_host}/authors/{author.serial}/entries/{entry.serial}"
        entry.save(update_fields=["url"])

        return Response(build_entry_payload(entry, request), status=201)

@api_view(["GET"])
def get_entry_fqid(request, entry_fqid):
    """
    Handles getting an entry by fqid.
    Friends-only posts require authentication.

    GET: Retrieve the entry based on its fqid.
    """
    require_auth_for_view(False)
    decoded_fqid = urllib.parse.unquote(entry_fqid)
    entry = get_object_or_404(Entry, url=decoded_fqid)

    requestingAuthor = get_requesting_author(request)

    # Ensure the user has permissions to view the entry.
    if not can_view_entry(entry, requestingAuthor, request.user):
        return Response({"error": "You do not have permission to view this entry."}, status=403)
    
    return Response(EntrySerializer(entry).data)

@api_view(["GET"])
def get_author_image_entry(request, author_serial, entry_serial):
    """
    Handles the retrieval of an image by author and entry serials.

    GET: Get an entry converted to binary as an image.
    """
    require_auth_for_view(False)
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    return serve_image(request, entry)

@api_view(["GET"])
def get_fqid_image_entry(request, entry_fqid):
    """
    Handles the retrieval of an image by fqid.

    GET: Get an entry converted to binary as an image.
    """
    require_auth_for_view(False)
    decoded_fqid = urllib.parse.unquote(entry_fqid)
    entry = get_object_or_404(Entry, url=decoded_fqid)
    return serve_image(request, entry)

def serve_image(request, entry):
    """
    Serves the image from an entry as binary, either from a locally stored image or from a base64 encoded image.
    """
    requestingAuthor = get_requesting_author(request)

    # Ensure the user has permissions to view the entry.
    if not can_view_entry(entry, requestingAuthor, request.user):
        return Response({"error": "You do not have permission to view this image entry."}, status=403)

    # Ensure correct content type
    if not entry.content_type.startswith("image") or entry.content_type.startswith("application/"):
        return Response({"error": f"The requested entry is not an image."}, status=404)
    
    # For standard locally stored images
    if entry.image_url:
        image = get_object_or_404(Image, url=entry.image_url)

        try:
            with image.image.open('rb') as f:
                image_data = f.read()
            
            mime_type, _ = mimetypes.guess_type(image.image.name)
            
            return HttpResponse(image_data, content_type=mime_type)
        except IOError:
            return Response({"error": "The requested image file could not be read."}, status=404)
    # For base64 encoded images (as per the project page)
    else:
        content = entry.content.strip()

        if content.startswith("data:"):
            try:
                content = content.split(",", 1)[1]
            except IndexError:
                pass

        try:
            image_data = base64.b64decode(content)
            mime_type = entry.content_type.replace(";base64", "").replace("; base64", "")

            if mime_type == "image" or not mime_type:
                try:
                    # Convert the raw bytes into a stream that Pillow can read
                    image_stream = io.BytesIO(image_data)
                    img = PILImage.open(image_stream)
                    
                    # Use pillow to get the format of a base64 image if not specified.
                    detected_format = img.format.lower()
                    
                    mime_type = f"image/{detected_format}"
                    
                except Exception as e:
                    print(f"Pillow Image Error: {e}")
                    return Response({"error": "The decoded data is not a valid or readable image."}, status=400)
            return HttpResponse(image_data, content_type=mime_type)
        except Exception:
            return Response({"error": "Invalid image data."}, status=400)