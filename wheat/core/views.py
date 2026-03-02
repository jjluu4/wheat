from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
import uuid

from .models import Author, Entry, Follow
from .forms import EntryForm
from .github import fetch_public_events
from .github_to_entries import save_event_as_entry


def index(request):
    return render(request, "exampleTemplate/index.html")


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
    
    if request.user.is_authenticated:
        isFollowing = True if request.user.author_profile.get_following().filter(serial=author.serial) else False
    else:
        isFollowing = False

    return render(
        request,
        "core/author_profile.html",
        {
            "author": author,
            "entries": entries,
            "is_owner": is_owner,
            "isFollowing": isFollowing,
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
    
    entries = Entry.get_entries(author).order_by("-published")

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
def edit_entry(request, author_serial, entry_id):
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, pk=entry_id, author=author)
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
def delete_entry(request, author_serial, entry_id):
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, pk=entry_id, author=author)
    if entry.visibility == "DELETED":
        return HttpResponseForbidden("This entry is already deleted.")

    if not author_owns_profile(request, author):
        return HttpResponseForbidden("You cannot delete another author's entries.")

    if request.method == "POST":
        entry.visibility = "DELETED"
        entry.save(update_fields=["visibility"])
        return redirect("author_profile", author_serial=author.serial)

    return render(request, "core/entry_confirm_delete.html", {"author": author, "entry": entry})