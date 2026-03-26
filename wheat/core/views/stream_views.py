from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import uuid

from ..models import Author, Entry

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
    
    allEntries = Entry.get_entries(author)
    if not request.user.is_staff:
        allEntries = allEntries.exclude(visibility="DELETED")
    allEntries = allEntries.order_by("-published")

    return render(
        request,
        "core/stream.html",
        {
            "author": author,
            "entries": allEntries,
        },
        )