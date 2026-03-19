from django.shortcuts import render
from ..models import Entry

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