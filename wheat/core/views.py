from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
import uuid
from rest_framework import status
from django.db import models
from django.utils import timezone

from .models import Author, Entry, Follow
from .forms import EntryForm
from .github import fetch_public_events
from .github_to_entries import save_event_as_entry

from .serializers import AuthorSerializer, EntrySerializer

def index(request):
    return render(request, "core/index.html")


def author_list(request):
    authors = Author.objects.order_by("displayName")
    return render(request, "core/author_list.html", {"authors": authors})


def author_profile(request, author_serial):
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
    return render(request, "registration/logged_out.html")

@login_required
def my_profile(request):
    """
    Send the logged-in user to THEIR author profile page.
    If a user exists without an Author profile (e.g., created via createsuperuser),
    create one automatically so this never breaks.
    """
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
    """
    Sends the logged-in user to their stream.
    If a user exists without an Author profile (e.g., created via createsuperuser),
    redirects to my_profile to create one automatically.
    """
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
    author = get_object_or_404(Author, serial=author_serial)

    if not author_owns_profile(request, author):
        return HttpResponseForbidden("You cannot create entries for another author.")

    if request.method == "POST":
        form = EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.author = author
            base_host = author.host.rstrip("/")
            entry.url = f"{base_host}/authors/{author.serial}/entries/{uuid.uuid4()}"
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
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, pk=entry_id, author=author)
    return edit_entry(request, author_serial=author.serial, entry_serial=entry.serial)


@login_required
def delete_entry(request, author_serial, entry_serial):
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

@login_required
def follow_author(request, author_serial):
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
    target = get_object_or_404(Author, user=request.user)

    requestList = Follow.objects.filter(
        target=target,
        status="REQUESTED"
    )

    return render(request, "core/follow_requests.html", {"requests": requestList, "author": target})

@login_required
def following(request, author_serial):
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
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, pk=entry_id, author=author)
    return delete_entry(request, author_serial=author.serial, entry_serial=entry.serial)

@api_view(['GET'])
def all_authors(request):
    page=int(request.GET.get('page', 1))
    size=int(request.GET.get('size', 5))

    if page < 1:
        page=1

    if size < 1:
        size=5    #same as no size

    offset=(page-1)*size

    serializer=AuthorSerializer(Author.objects.all()[offset:offset+size], many=True)

    return Response({"type": "authors", "authors": serializer.data})

@api_view(['GET', 'PUT'])
def single_author(request, author_serial): #support GET and PUT
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

@api_view(['GET', 'PUT', 'DELETE'])
def single_entry(request, author_serial, entry_serial):
    
    if not request.user.is_authenticated:
        return Response(data={"error": "Authentication required to for entry API endpoint"},status=401)    
    
    entry = get_object_or_404(Entry, serial=entry_serial)
    requestingAuthor = request.user.author_profile
    entryAuthor = get_object_or_404(Author, serial=author_serial)
    
    if request.method == 'GET':    
        
        viewable_entries = Entry.get_entries(requestingAuthor) | Entry.objects.filter(author=requestingAuthor).exclude(visibility="DELETED")
        viewable = True if viewable_entries.filter(serial=entry.serial) or request.user.is_staff else False
        
        if viewable:
            author_serial = AuthorSerializer(entryAuthor).data
            entry_serial = EntrySerializer(entry, context={'author': author_serial}).data
            entry_serial['author'] = author_serial
            return Response(entry_serial)
        else:
            return Response(data={"error": "You don't have permission to view this entry"},status=403)
    
    elif request.method == 'PUT':
        if not hasattr(request.user,'author_profile') or request.user.author_profile!=entryAuthor:
            return Response(data={"error": "You don't have permission to update this profile"},status=403)
        
        for field in ['content', 'content_type', 'image_url', 'visibility']:
            if field in request.data:
                setattr(entry, field, request.data[field])        
        
        entry.save()
        
        author_serial = AuthorSerializer(entryAuthor).data
        entry_serial = EntrySerializer(entry, context={'author': author_serial}).data
        entry_serial['author'] = author_serial
        return Response(entry_serial)        
        
    
    elif request.method == 'DELETE':
        if entryAuthor == requestingAuthor.serial or request.user.is_staff:
            return Response(data={"error": "You don't have permission to delete this entry."},status=403)
        
        try:
            entry = Entry.objects.get(serial=entry.serial)

        except entry.DoesNotExist:
            return Response({"error": "Entry not found"}, status=status.HTTP_404_NOT_FOUND)

        #Delete the item from the database 
        entry.delete()
            
        return Response(data={"deleted": "Entry has been deleted."},status=204)
            
        
@api_view(['GET', 'POST'])
def author_entries(request, author_serial):
    
    if not request.user.is_authenticated:
        return Response(data={"error": "Authentication required to view entry"},status=401)
    
    author = get_object_or_404(Author, serial=author_serial)
    requestingAuthor = request.user.author_profile
    
    if request.method == 'GET':
        page=int(request.GET.get('page', 1))
        size=int(request.GET.get('size', 5))
        
        if page < 1:
            page=1
        
        if size < 1:
            size=5    #same as no size
        
        offset=(page-1)*size
        
        entries = Entry.objects.filter(author=author).exclude(visibility="DELETED")
        
        friend = author.get_friends().filter(serial=requestingAuthor.serial)
        follower = author.get_followers().filter(serial=requestingAuthor.serial)
        
        # Retrieve entries based on if requesting Author is friend/follower/unaffiliated
        if len(friend) > 0 or (author_serial == requestingAuthor.serial) or request.user.is_staff:
            entries = Entry.objects.filter(author=author).exclude(visibility="DELETED")
        elif len(follower) > 0:
            entries = Entry.objects.filter(author=author).exclude(visibility in ["DELETED", "FRIENDS"])
        else:
            entries = Entry.objects.filter(author=author, visibility="PUBLIC")
        
        serializer = EntrySerializer(entries[offset:offset+size], many=True)
        entryData = serializer.data
        
        # Put Serialized Author data into entryData
        for i in range(len(entryData)):
            entryData[i]["author"] = AuthorSerializer(entries[i].author).data
        
        return Response({"type": "entries", "entries": entryData})
    
    elif request.method == 'POST':
        if author.serial == requestingAuthor.serial:
            data = request.data
            authorData = data['author']
            data['author'] = author.pk
            entry = EntrySerializer(data=request.data)
            if entry.is_valid():
                base_host = author.host.rstrip("/")
                entry.validated_data['url'] = f"{base_host}/authors/{author.serial}/entries/{uuid.uuid4()}"
                #entry.validated_data['published'] = models.DateTimeField(default=timezone.now)
                entry.save()
                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response(entry.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data={"error": "You cannot add entries to another user"},status=403)