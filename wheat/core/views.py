from django.shortcuts import render, get_object_or_404, redirect
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


def author_edit(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)

    if request.method == "POST":
        author.displayName = request.POST.get("displayName", author.displayName)
        author.github = request.POST.get("github", author.github)
        author.description = request.POST.get("description", author.description)
        author.profileImage = request.POST.get("profileImage", author.profileImage)

        author.save()

        return redirect("author_profile", author_serial=author.serial)

    return render(request, "core/author_edit.html", {"author": author})