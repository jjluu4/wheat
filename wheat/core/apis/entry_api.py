from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
import uuid
from rest_framework import status
from django.db import models
import re

from ..models import Author, Entry, Follow, Comment, EntryLike, CommentLike
from ..forms import EntryForm
from ..github import fetch_public_events
from ..github_to_entries import save_event_as_entry

from ..serializers import AuthorSerializer, EntrySerializer, CommentSerializer, CommentLikeSerializer, EntryLikeSerializer
from ..permissions import (
    get_requesting_author,
    is_friend,
    can_view_entry,
    can_view_comment,
    filter_comments_for_viewer,
)
from ..helpers import get_pagination_params, build_entry_payload

@api_view(["GET", "PUT", "DELETE"])
def single_entry(request, author_serial, entry_serial):
    """
    Handles operations on a single entry.
    """
    entryAuthor = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=entryAuthor)
    requestingAuthor = get_requesting_author(request)

    if request.method == "GET":
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