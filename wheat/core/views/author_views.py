from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
import uuid

from ..models import Author, Entry, Follow
from ..permissions import get_requesting_author, is_friend
from ..github import fetch_public_events
from ..github_to_entries import save_event_as_entry

def author_list(request):
    """Render a list of all authors ordered by display name."""
    authors = Author.objects.order_by("displayName")
    return render(request, "core/author_list.html", {"authors": authors})


def author_profile(request, author_serial):
    """Show an author's profile page and their visible entries."""
    author = get_object_or_404(Author, serial=author_serial)
    if author.github:
        try:
            events = fetch_public_events(author.github, per_page=5)
            for e in events:
                save_event_as_entry(e, author)
        except Exception:
            pass

    is_owner = (
        request.user.is_authenticated
        and (author.user_id == request.user.id or request.user.is_staff)
    )

    if is_owner:
        entries = Entry.objects.filter(author=author)
        if not request.user.is_staff:
            entries = entries.exclude(visibility="DELETED")
    else:
        viewer = get_requesting_author(request)
        if viewer is None:
            entries = Entry.objects.filter(author=author, visibility="PUBLIC")
        else:
            q = Q(visibility="PUBLIC")
            if Follow.objects.filter(actor=viewer, target=author, status="ACCEPTED").exists():
                q |= Q(visibility="UNLISTED")
            if is_friend(author, viewer):
                q |= Q(visibility="FRIENDS")
            entries = Entry.objects.filter(author=author).filter(q)
            # Non-admin viewers should not see deleted entries.
            entries = entries.exclude(visibility="DELETED")

    entries = entries.order_by("-published")

    followStatus = None
    viewer_for_follow = get_requesting_author(request)
    if viewer_for_follow is not None:
        follow = Follow.objects.filter(actor=viewer_for_follow, target=author).first()
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