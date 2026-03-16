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

@api_view(['GET'])
def all_authors(request):
    """
    Retrieves a paginated list of all authors on this node

    parameters:
        - page: Page number (default: 1)
        - size: Number of authors per page (default: 5)
    """
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
        serializer=AuthorSerializer(author)
        return Response(serializer.data)

    elif request.method=='PUT':
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