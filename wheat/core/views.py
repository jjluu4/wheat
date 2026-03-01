from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
import uuid

from .models import Author, Entry
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

    entries = (
        Entry.objects.filter(author=author, visibility="PUBLIC")
        .order_by("-published")
    )

    return render(
        request,
        "core/author_profile.html",
        {
            "author": author,
            "entries": entries,
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