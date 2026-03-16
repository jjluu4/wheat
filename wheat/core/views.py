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

from .models import Author, Entry, Follow, Comment, EntryLike, CommentLike
from .forms import EntryForm
from .github import fetch_public_events
from .github_to_entries import save_event_as_entry

from .serializers import AuthorSerializer, EntrySerializer, CommentSerializer, CommentLikeSerializer, EntryLikeSerializer
from .permissions import (
    get_requesting_author,
    is_friend,
    can_view_entry,
    can_view_comment,
    filter_comments_for_viewer,
)

#
# TODO: this is approaching godfile, we should probably split this for pt2
#

LIKES_PAGE_SIZE = 50

def index(request):
    """
    show all public entries if logged out, otherwise show users stream and any public entries, kinda like an explore page
    """
    public_entries = Entry.objects.filter(visibility="PUBLIC")

    entries_qs = public_entries
    author = None

    if request.user.is_authenticated and hasattr(request.user, "author_profile"):
        author = request.user.author_profile
        stream_entries = (
            Entry.get_entries(author)
            .exclude(author__serial=author.serial)
        )
        entries_qs = (public_entries | stream_entries)

    entries = (
        entries_qs
        .select_related("author")
        .order_by("-published")
        .distinct()
    )

    return render(
        request,
        "core/index.html",
        {
            "entries": entries,
            "author": author,
        },
    )


def author_list(request):
    """Render a list of all authors ordered by display name."""
    authors = Author.objects.order_by("displayName")
    return render(request, "core/author_list.html", {"authors": authors})


def author_profile(request, author_serial):
    """Show an author's profile page and their visible entries."""
    author = get_object_or_404(Author, serial=author_serial)

    # Auto-import newest GitHub events as PUBLIC entries
    # (should not duplicate if save_event_as_entry uses unique URL)
    if author.github:
        try:
            events = fetch_public_events(author.github, per_page=5)
            for e in events:
                save_event_as_entry(e, author)
        except Exception:
            # Don't break the profile page if GitHub API fails
            pass

    is_owner = (
        request.user.is_authenticated
        and (author.user_id == request.user.id or request.user.is_staff)
    )

    if is_owner:
        entries = Entry.objects.filter(author=author).exclude(visibility="DELETED")
    else:
        entries = Entry.objects.filter(author=author, visibility="PUBLIC")

    entries = entries.order_by("-published")

    followStatus = None
    if request.user.is_authenticated:
        follow = Follow.objects.filter(
            actor=request.user.author_profile,
            target=author
        ).first()

        if follow:
            followStatus = follow.status


    return render(
        request,
        "core/author_profile.html",
        {
            "author": author,
            "entries": entries,
            "is_owner": is_owner,
            "followStatus": followStatus,
        },
    )


@login_required
def author_edit(request, author_serial):
    """Allow an authenticated author (or staff) to edit their profile."""
    author = get_object_or_404(Author, serial=author_serial)

    # Only the owner (or staff) can edit
    if (author.user_id is None or author.user_id != request.user.id) and not request.user.is_staff:
        return HttpResponseForbidden("You cannot edit someone else's profile.")

    if request.method == "POST":
        author.displayName = request.POST.get("displayName", author.displayName)
        author.github = request.POST.get("github", author.github)
        author.description = request.POST.get("description", author.description)
        author.profileImage = request.POST.get("profileImage", author.profileImage)

        author.save()

        return redirect("author_profile", author_serial=author.serial)

    return render(request, "core/author_edit.html", {"author": author})


def signup(request):
    """Handle user signup and auto-create an Author profile."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Auto-create an Author profile for this new user
            if not hasattr(user, "author_profile"):
                base = request.build_absolute_uri("/").rstrip("/")
                author_serial = uuid.uuid4()

                Author.objects.create(
                    user=user,
                    serial=author_serial,
                    host=f"{base}/api/",
                    url=f"{base}/api/authors/{author_serial}",
                    web=f"{base}/authors/{author_serial}/",
                    displayName=user.username,
                    github=f"https://github.com/{user.username}",
                    description="",
                    profileImage="https://placehold.co/150x150.png",
                )

            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})

def logged_out(request):
    """Simple logged-out confirmation page."""
    return render(request, "registration/logged_out.html")

@login_required
def my_profile(request):
    """Redirect the logged-in user to their own author profile, creating one if needed."""
    try:
        author = request.user.author_profile
    except Author.DoesNotExist:
        base = request.build_absolute_uri("/").rstrip("/")
        author_serial = uuid.uuid4()
        author = Author.objects.create(
            user=request.user,
            serial=author_serial,
            host=f"{base}/api/",
            url=f"{base}/api/authors/{author_serial}",
            web=f"{base}/authors/{author_serial}/",
            displayName=request.user.username,
            github=f"https://github.com/{request.user.username}",
            description="",
            profileImage="https://placehold.co/150x150.png",
        )

    return redirect("author_profile", author_serial=author.serial)

@login_required
def my_stream(request):
    """Render the logged-in user's stream of entries from others."""
    try:
        author = request.user.author_profile
    except Author.DoesNotExist:
        base = request.build_absolute_uri("/").rstrip("/")
        author_serial = uuid.uuid4()
        author = Author.objects.create(
            user=request.user,
            serial=author_serial,
            host=f"{base}/api/",
            url=f"{base}/api/authors/{author_serial}",
            web=f"{base}/authors/{author_serial}/",
            displayName=request.user.username,
            github=f"https://github.com/{request.user.username}",
            description="",
            profileImage="https://placehold.co/150x150.png",
        )
    
    allEntries = Entry.get_entries(author).order_by("-published")
    entries = allEntries.exclude(author__serial=author.serial)    

    return render(
        request,
        "core/stream.html",
        {
            "author": author,
            "entries": entries,
        },
        )


def author_owns_profile(request, author):
    #as an author, other authors cannot modify my entries, so that I don't get impersonated.
    if (author.user_id is None or author.user_id != request.user.id) and not request.user.is_staff:
        return False
    return True


@login_required
def create_entry(request, author_serial):
    """HTML view to create a new entry for the given author."""
    author = get_object_or_404(Author, serial=author_serial)

    if not author_owns_profile(request, author):
        return HttpResponseForbidden("You cannot create entries for another author.")

    if request.method == "POST":
        form = EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.author = author
            base_host = author.host.rstrip("/")
            entry.url = f"{base_host}/authors/{author.serial}/entries/{entry.serial}"
            entry.save()
            return redirect("author_profile", author_serial=author.serial)
    else:
        form = EntryForm(
            initial={
                "content_type": "text/plain",
                "visibility": "PUBLIC",
            }
        )

    return render(request, "core/entry_form.html", {"author": author, "form": form, "is_edit": False})

@login_required
def edit_entry(request, author_serial, entry_serial):
    """HTML view to edit an existing entry by UUID."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=author)
    if entry.visibility == "DELETED":
        return HttpResponseForbidden("You cannot edit a deleted entry.")
    if not author_owns_profile(request, author):
        return HttpResponseForbidden("You cannot edit another author's entries.")
    if request.method == "POST":
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect("author_profile", author_serial=author.serial)
    else:
        form = EntryForm(instance=entry)

    return render(request, "core/entry_form.html", {"author": author, "form": form, "is_edit": True, "entry": entry})


@login_required
def edit_entry_legacy(request, author_serial, entry_id):
    """Backward-compatible HTML edit view that accepts a legacy integer entry id."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, pk=entry_id, author=author)
    return edit_entry(request, author_serial=author.serial, entry_serial=entry.serial)


@login_required
def delete_entry(request, author_serial, entry_serial):
    """HTML view to soft-delete an entry by setting its visibility to DELETED."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=author)
    if entry.visibility == "DELETED":
        return HttpResponseForbidden("This entry is already deleted.")

    if not author_owns_profile(request, author):
        return HttpResponseForbidden("You cannot delete another author's entries.")

    if request.method == "POST":
        entry.visibility = "DELETED"
        entry.save(update_fields=["visibility"])
        return redirect("author_profile", author_serial=author.serial)

    return render(request, "core/entry_confirm_delete.html", {"author": author, "entry": entry})

def view_entry(request, author_serial, entry_serial):
    """HTML view for a single entry, enforcing visibility and friendship rules."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=author)

    if entry.visibility == "DELETED":
        return HttpResponseForbidden("This entry has been deleted.")

    elif entry.visibility == "PUBLIC" or entry.visibility == "UNLISTED":
        return render(request, "core/view_entry.html", {"entry": entry, "author": author})
    
    else:
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You do not have permission to view this entry.")
        
        requestingAuthor = getattr(request.user, "author_profile", None)
        is_owner = request.user.is_staff or requestingAuthor == author
        is_friend = requestingAuthor is not None and author.get_friends().filter(serial=requestingAuthor.serial).exists()

        if is_owner or is_friend:
            return render(request, "core/view_entry.html", {"entry": entry, "author": author})
        
        return HttpResponseForbidden("You do not have permission to view this entry.")


@login_required
def follow_author(request, author_serial):
    """Create or re-request a follow from the current user to the target author."""
    actor = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, serial=author_serial)

    follow, created = Follow.objects.get_or_create(
        actor=actor,
        target=target
    )

    if not created and (follow.status == "DECLINED" or follow.status == "REJECTED"):
        follow.status = "REQUESTED"
        follow.save()
    
    return redirect("author_profile", author_serial=target.serial)

@login_required
def accept_follow(request, author_serial):
    """Accept a pending follow request from the specified author."""
    target = get_object_or_404(Author, user=request.user)
    actor = get_object_or_404(Author, serial=author_serial)

    try:
        follow = Follow.objects.get(
            actor=actor,
            target=target,
            status="REQUESTED"
        )

        follow.status = "ACCEPTED"
        follow.save()

        return redirect("author_profile", author_serial=target.serial)
    
    except Follow.DoesNotExist:
        return HttpResponseNotFound("Follow request cannot be found.")

@login_required
def reject_follow(request, author_serial):
    """Reject a pending follow request from the specified author."""
    target = get_object_or_404(Author, user=request.user)
    actor = get_object_or_404(Author, serial=author_serial)

    try:
        follow = Follow.objects.get(
            actor=actor,
            target=target,
            status="REQUESTED"
        )

        follow.status = "REJECTED"
        follow.save()

        return redirect("author_profile", author_serial=target.serial)
    
    except Follow.DoesNotExist:
        return HttpResponseNotFound("Follow request cannot be found.")

@login_required
def follow_requests(request, author_serial):
    """HTML view listing pending follow requests for the current user."""
    target = get_object_or_404(Author, user=request.user)

    requestList = Follow.objects.filter(
        target=target,
        status="REQUESTED"
    )

    return render(request, "core/follow_requests.html", {"requests": requestList, "author": target})

@login_required
def following(request, author_serial):
    """HTML view listing authors the current user is following."""
    author = get_object_or_404(Author, user=request.user)

    followingQuery = Follow.objects.filter(
        actor=author,
        status="ACCEPTED"
    ).select_related("target")

    followingList = []
    for q in followingQuery:
        followingList.append(q.target)

    return render(request, "core/follow_list.html", {"authors": followingList, "follow_type": "Following", "author": author})

@login_required
def followers(request, author_serial):
    """HTML view listing authors who follow the current user."""
    author = get_object_or_404(Author, user=request.user)

    followerQuery = Follow.objects.filter(
        target=author,
        status="ACCEPTED"
    ).select_related("actor")

    followerList = []
    for q in followerQuery:
        followerList.append(q.actor)

    return render(request, "core/follow_list.html", {"authors": followerList, "follow_type": "Followers", "author": author})

@login_required
def unfollow(request, author_serial):
    """Remove an accepted follow relationship from the current user to the target author."""
    actor = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, serial=author_serial)

    try:
        follow = Follow.objects.get(
            actor=actor,
            target=target,
            status="ACCEPTED"
        )

        follow.delete()

        return redirect("author_profile", author_serial=target.serial)
    
    except Follow.DoesNotExist:
        return HttpResponseNotFound("Follow request cannot be found.")

@login_required
def delete_entry_legacy(request, author_serial, entry_id):
    """Backward-compatible HTML delete view that accepts a legacy integer entry id."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, pk=entry_id, author=author)
    return delete_entry(request, author_serial=author.serial, entry_serial=entry.serial)

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

@api_view(['GET'])
def get_following_api(request, author_serial):
    """
    Retrieves the list of authors that the specified author is following
    
    Requires authentication as the author
    """
    author = get_object_or_404(Author, serial=author_serial)

    if not request.user.is_authenticated:
        return Response(data="Authentication is required to retrieve the following list.", status=401)
    
    if author.user != request.user:
        return Response(data="You don't have permission to view this following list.", status=403)
    
    followingList = author.get_following()
    serializer = AuthorSerializer(followingList, many=True)

    return Response({
        "type": "following", 
        "following": serializer.data
        })

@api_view(['GET'])
def get_follow_requests_api(request, author_serial):
    """
    Retrieves all pending follow requests for the specified author, returns a list of follow request objects

    Requires authentication as the author
    """
    author = get_object_or_404(Author, serial=author_serial)

    if not request.user.is_authenticated:
        return Response(data="Authentication is required to retrieve these follow requests.", status=401)
    
    if author.user != request.user:
        return Response(data="You don't have permission to view these follow requests.", status=403)
    
    requestList = Follow.objects.filter(target=author, status="REQUESTED")

    serializedAuthor = AuthorSerializer(author).data

    data = []
    for request in requestList:
        serializedActor = AuthorSerializer(request.actor).data
        data.append({
            "type": "follow",
            "summary": f"{request.actor} wants to follow {request.target}",
            "actor": serializedActor,
            "object": serializedAuthor
        })

    return Response(data)


def get_pagination_params(request, default_size=5):
    """Parse page/size query params and return sanitized pagination values."""
    try:
        page = int(request.GET.get("page", 1))
        if page < 1:
            page = 1
    except (TypeError, ValueError):
        page = 1

    try:
        size = int(request.GET.get("size", default_size))
        if size < 1:
            size = default_size
    except (TypeError, ValueError):
        size = default_size

    return page, size


def build_entry_likes_url(request, entry):
    base_url = request.build_absolute_uri("/").rstrip("/")
    return f"{base_url}/api/authors/{entry.author.serial}/entries/{entry.serial}/likes/"


def build_comment_likes_url(request, comment):
    base_url = request.build_absolute_uri("/").rstrip("/")
    return f"{base_url}/api/authors/{comment.entry.author.serial}/entries/{comment.entry.serial}/comments/{comment.serial}/likes/"


def build_like_url(request, author, like_serial):
    base_url = request.build_absolute_uri("/").rstrip("/")
    return f"{base_url}/api/authors/{author.serial}/liked/{like_serial}/"


def build_likes_collection(queryset, serializer_class, collection_id, page=1, size=LIKES_PAGE_SIZE):
    offset = (page - 1) * size
    total = queryset.count()
    page_items = list(queryset[offset : offset + size])
    return {
        "type": "likes",
        "id": collection_id,
        "page_number": page,
        "size": size,
        "count": total,
        "src": serializer_class(page_items, many=True).data,
    }


def serialize_like_item(like):
    """Serialize either an EntryLike or CommentLike into its API representation."""
    if isinstance(like, EntryLike):
        return EntryLikeSerializer(like).data
    return CommentLikeSerializer(like).data


def build_mixed_likes_collection(items, collection_id, page, size):
    offset = (page - 1) * size
    page_items = items[offset : offset + size]
    return {
        "type": "likes",
        "id": collection_id,
        "page_number": page,
        "size": size,
        "count": len(items),
        "src": [serialize_like_item(item) for item in page_items],
    }


def build_entry_payload(entry, request):
    payload = EntrySerializer(entry).data
    payload["author"] = AuthorSerializer(entry.author).data
    likes_qs = EntryLike.objects.filter(entry=entry).select_related("author").order_by("-published")
    payload["likes"] = build_likes_collection(
        likes_qs,
        EntryLikeSerializer,
        build_entry_likes_url(request, entry),
    )
    return payload


def build_comment_payload(comment, request):
    comment_data = CommentSerializer(comment, context={"request": request}).data
    comment_data["entry"] = f"{request.build_absolute_uri('/').rstrip('/')}/api/authors/{comment.entry.author.serial}/entries/{comment.entry.serial}/"
    likes_qs = CommentLike.objects.filter(comment=comment).select_related("author").order_by("-published")
    comment_data["likes"] = build_likes_collection(
        likes_qs,
        CommentLikeSerializer,
        build_comment_likes_url(request, comment),
    )
    return comment_data


ENTRY_OBJECT_RE = re.compile(r"/api/authors/(?P<author>[0-9a-f-]+)/entries/(?P<entry>[0-9a-f-]+)/?$")
COMMENT_OBJECT_RE = re.compile(r"/api/authors/(?P<author>[0-9a-f-]+)/commented/(?P<comment>[0-9a-f-]+)/?$")


def resolve_like_target(object_url):
    entry_match = ENTRY_OBJECT_RE.search(object_url or "")
    if entry_match:
        entry = get_object_or_404(
            Entry,
            serial=entry_match.group("entry"),
            author__serial=entry_match.group("author"),
        )
        return "entry", entry

    comment_match = COMMENT_OBJECT_RE.search(object_url or "")
    if comment_match:
        comment = get_object_or_404(
            Comment,
            serial=comment_match.group("comment"),
            author__serial=comment_match.group("author"),
        )
        return "comment", comment

    return None, None

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

@api_view(['GET', 'POST'])
def author_commented(request, author_serial):
    """
    Handles operations on an authors comments

    GET: Retrieve paginated list of comments made by the author
    POST: Create a new comment as the author. Requires authentication and the comment must be associated with a valid entry URL
    """
    author=get_object_or_404(Author, serial=author_serial)

    if request.method=='GET':
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
            "page_number": page,
            "size": size,
            "count": total,
            "src": data,
        })

    elif request.method=='POST':
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
            url=f"{request.build_absolute_uri('/')}api/authors/{author_serial}/commented/{comment_serial}/",
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
    author=get_object_or_404(Author, serial=author_serial)
    comment=get_object_or_404(Comment, serial=comment_serial, author=author)

    entry=comment.entry

    requesting_author = get_requesting_author(request)

    if not can_view_comment(comment, requesting_author, request.user):
        return Response({"error": "You don't have permission to view this comment"}, status=403)

    comment_data = build_comment_payload(comment, request)
    comment_data['web']=f"{request.build_absolute_uri('/').rstrip('/')}/authors/{author.serial}/comments/{comment.serial}"

    return Response(comment_data)

@api_view(['GET'])
def entry_comments(request, author_serial, entry_serial):
    """
    Retrieves paginated comments for a specific entry

    Depends on post visibility (PUBLIC/UNLISTED viewable by anyone, FRIENDS viewable by friends, otherwise requires authentication as author)
    """
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
        "page_number": page,
        "size": size,
        "count": visible_comments.count(),
        "src": data,
    })


@api_view(["GET", "POST"])
def author_liked(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)

    if request.method == "POST":
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        requesting_author = get_requesting_author(request)
        if not requesting_author or requesting_author != author:
            return Response({"error": "Cannot like as another author"}, status=403)

        object_url = request.data.get("object")
        if not object_url:
            return Response({"error": "Object URL is required"}, status=400)

        target_type, target = resolve_like_target(object_url)
        if not target_type:
            return Response({"error": "Invalid object URL"}, status=400)

        if target_type == "entry":
            if not can_view_entry(target, requesting_author, request.user):
                return Response({"error": "You don't have permission to like this entry"}, status=403)

            existing_like = EntryLike.objects.filter(author=author, entry=target).select_related("author", "entry").first()
            if existing_like:
                return Response(EntryLikeSerializer(existing_like).data, status=200)

            like = EntryLike.objects.create(
                author=author,
                entry=target,
                url=build_like_url(request, author, uuid.uuid4()),
            )
            like.url = build_like_url(request, author, like.serial)
            like.save(update_fields=["url"])
            return Response(EntryLikeSerializer(like).data, status=201)

        if not can_view_comment(target, requesting_author, request.user):
            return Response({"error": "You don't have permission to like this comment"}, status=403)

        existing_like = CommentLike.objects.filter(author=author, comment=target).select_related("author", "comment").first()
        if existing_like:
            return Response(CommentLikeSerializer(existing_like).data, status=200)

        like = CommentLike.objects.create(
            author=author,
            comment=target,
            url=build_like_url(request, author, uuid.uuid4()),
        )
        like.url = build_like_url(request, author, like.serial)
        like.save(update_fields=["url"])
        return Response(CommentLikeSerializer(like).data, status=201)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    requesting_author = get_requesting_author(request)

    entry_likes = [
        like
        for like in EntryLike.objects.filter(author=author).select_related("author", "entry", "entry__author")
        if can_view_entry(like.entry, requesting_author, request.user)
    ]
    comment_likes = [
        like
        for like in CommentLike.objects.filter(author=author).select_related("author", "comment", "comment__entry", "comment__entry__author", "comment__author")
        if can_view_comment(like.comment, requesting_author, request.user)
    ]
    items = sorted(entry_likes + comment_likes, key=lambda like: like.published, reverse=True)

    collection_id = f"{request.build_absolute_uri('/').rstrip('/')}/api/authors/{author.serial}/liked/"
    return Response(build_mixed_likes_collection(items, collection_id, page, size))


@api_view(["GET"])
def entry_likes(request, author_serial, entry_serial):
    """API endpoint listing likes on a specific entry,"""
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    requesting_author = get_requesting_author(request)

    if not can_view_entry(entry, requesting_author, request.user):
        if not request.user.is_authenticated and entry.visibility == "FRIENDS":
            return Response({"error": "Authentication required"}, status=401)
        return Response({"error": "You don't have permission to view likes on this entry"}, status=403)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    likes_qs = EntryLike.objects.filter(entry=entry).select_related("author").order_by("-published")
    return Response(build_likes_collection(likes_qs, EntryLikeSerializer, build_entry_likes_url(request, entry), page, size))


@api_view(["GET"])
def comment_likes(request, author_serial, entry_serial, comment_serial):
    """API endpoint listing likes on a specific comment"""
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    comment = get_object_or_404(Comment, serial=comment_serial, entry=entry)
    requesting_author = get_requesting_author(request)

    if not can_view_comment(comment, requesting_author, request.user):
        if not request.user.is_authenticated and entry.visibility == "FRIENDS":
            return Response({"error": "Authentication required"}, status=401)
        return Response({"error": "You don't have permission to view likes on this comment"}, status=403)

    page, size = get_pagination_params(request, default_size=LIKES_PAGE_SIZE)
    likes_qs = CommentLike.objects.filter(comment=comment).select_related("author").order_by("-published")
    return Response(build_likes_collection(likes_qs, CommentLikeSerializer, build_comment_likes_url(request, comment), page, size))
