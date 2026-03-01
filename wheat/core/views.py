from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
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


def author_edit(request, author_id):
    author = get_object_or_404(Author, pk=author_id)

    if request.method == "POST":
        author.displayName = request.POST.get("displayName", author.displayName)
        author.github = request.POST.get("github", author.github)
        author.description = request.POST.get("description", author.description)
        author.profileImage = request.POST.get("profileImage", author.profileImage)

        author.save()
        return redirect("author_profile", author_id=author.id)

    return render(request, "core/author_edit.html", {"author": author})