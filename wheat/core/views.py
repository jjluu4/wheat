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

from .models import Author, Entry, Follow, Comment
from .forms import EntryForm
from .github import fetch_public_events
from .github_to_entries import save_event_as_entry

from .serializers import AuthorSerializer, EntrySerializer, CommentSerializer, CommentLikeSerializer, EntryLikeSerializer

#
# TODO: this is approaching godfile, we should probably split this for pt2
#

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

@api_view(["GET", "PUT", "DELETE"])
def single_entry(request, author_serial, entry_serial):
   
    entryAuthor = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=entryAuthor)

    # If the requester is authenticated, capture their Author profile (if any)
    requestingAuthor = None
    if request.user.is_authenticated and hasattr(request.user, "author_profile"):
        requestingAuthor = request.user.author_profile

    if request.method == "GET":
        if entry.visibility == "DELETED":
            return Response({"error": "Entry not found"}, status=404)

        # PUBLIC and UNLISTED entries are viewable by anyone
        if entry.visibility in ("PUBLIC", "UNLISTED"):
            serializedAuthor = AuthorSerializer(entryAuthor).data
            payload = EntrySerializer(entry).data
            payload["author"] = serializedAuthor
            return Response(payload, status=200)

        
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        if request.user.is_staff or (requestingAuthor and requestingAuthor == entryAuthor):
            serializedAuthor = AuthorSerializer(entryAuthor).data
            payload = EntrySerializer(entry).data
            payload["author"] = serializedAuthor
            return Response(payload, status=200)

        if requestingAuthor and entryAuthor.get_friends().filter(serial=requestingAuthor.serial).exists():
            serializedAuthor = AuthorSerializer(entryAuthor).data
            payload = EntrySerializer(entry).data
            payload["author"] = serializedAuthor
            return Response(payload, status=200)

        return Response({"error": "You don't have permission to view this entry"}, status=403)

    elif request.method == "PUT":
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        if not hasattr(request.user, "author_profile") or request.user.author_profile != entryAuthor:
            return Response({"error": "You don't have permission to edit this entry"}, status=403)

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

        serializedAuthor = AuthorSerializer(entryAuthor).data
        payload = EntrySerializer(entry).data
        payload["author"] = serializedAuthor
        return Response(payload, status=200)

    elif request.method == "DELETE":
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        if request.user.is_staff or (hasattr(request.user, "author_profile") and request.user.author_profile == entryAuthor):
      
            entry.visibility = "DELETED"
            entry.save(update_fields=["visibility"])
            return Response(status=204)

        return Response({"error": "You don't have permission to delete this entry."}, status=403)
            
        
@api_view(["GET", "POST"])
def author_entries(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)

    requestingAuthor = None
    if request.user.is_authenticated and hasattr(request.user, "author_profile"):
        requestingAuthor = request.user.author_profile

    if request.method == "GET":
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
        serializer = EntrySerializer(page_entries, many=True)
        entryData = serializer.data

        serializedAuthor = AuthorSerializer(author).data
        for item in entryData:
            item["author"] = serializedAuthor

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
        visibility = request.data.get("visibility", "PUBLIC")
        if visibility not in ("PUBLIC", "UNLISTED", "FRIENDS"):
            visibility = "PUBLIC"

        if content_type == "image" and not image_url:
            return Response({"error": "imageUrl is required for image entries"}, status=400)

        entry = Entry.objects.create(
            author=author,
            url="",
            content=content,
            content_type=content_type,
            image_url=image_url,
            visibility=visibility,
        )

        base_host = (author.host or "").rstrip("/")
        entry.url = f"{base_host}/authors/{author.serial}/entries/{entry.serial}"
        entry.save(update_fields=["url"])

        serializedAuthor = AuthorSerializer(author).data
        payload = EntrySerializer(entry).data
        payload["author"] = serializedAuthor
        return Response(payload, status=201)

@api_view(['GET', 'POST'])
def author_commented(request, author_serial):
    author=get_object_or_404(Author, serial=author_serial)

    if request.method=='GET':
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

        offset=(page - 1) * size

        comments=Comment.objects.filter(author=author).select_related('author', 'entry').order_by('-published')

        requestingAuthor=None
        if request.user.is_authenticated and hasattr(request.user, 'author_profile'):
            requestingAuthor=request.user.author_profile

        total=comments.count()
        page_comments=list(comments[offset:offset+size])

        data=[]
        for comment in page_comments:
            serializer=CommentSerializer(comment, context={'request': request})
            data.append(serializer.data)

        return Response({ 
            #this is missing 'web' and 'id' fields for networking later
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
        except Exception as e:
            return Response({"error": f"Invalid entry URL"}, status=400)

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

        serializer=CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=201)


@api_view(['GET'])
def entry_comments(request, author_serial, entry_serial):
    entry=get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    entry_author=entry.author

    requesting_author=None
    if request.user.is_authenticated and hasattr(request.user, 'author_profile'):
        requesting_author=request.user.author_profile

    friend=entry.visibility=='FRIENDS' and requesting_author and entry_author.get_friends().filter(serial==requesting_author.serial).exists()

    if not (requesting_author==entry_author or request.user.is_staff or entry.visibility.upper() in ['PUBLIC', 'UNLISTED'] or friend):
        return Response({"error": "You don't have permission to view comments on this entry"}, status=403)

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

    offset=(page - 1) * size

    comments=Comment.objects.filter(entry=entry).select_related('author').order_by('-published')
    base_url=request.build_absolute_uri('/').rstrip('/')

    data=[]
    for comment in list(comments[offset:offset+size]):
        serializer=CommentSerializer(comment, context={'request': request})
        comment_data=serializer.data

        comment_data['entry']=f"{base_url}/api/authors/{entry_author.serial}/entries/{entry.serial}/"
        
        comment_data['likes']={ #PLACEHOLDER, likes not done yet
            #this is missing 'web' and 'id' fields for networking later
            "type": "likes",
            "page_number": 1,
            "size": 50,
            "count": 0,
            "src": [],
        }
        
        data.append(comment_data)

    return Response({
        #this is missing 'web' and 'id' fields for networking later
        "type": "comments",
        "page_number": page,
        "size": size,
        "count": comments.count(),
        "src": data,
    })