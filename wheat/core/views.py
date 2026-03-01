from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Author, Entry

def index(request):
    return render(request, "exampleTemplate/index.html")

def author_profile(request, author_id):
    author = get_object_or_404(Author, pk=author_id)

    entries = Entry.objects.filter(
        author=author,
        visibility="PUBLIC"
    ).order_by("-published")

    return render(request, "core/author_profile.html", {
        "author": author,
        "entries": entries,
    })