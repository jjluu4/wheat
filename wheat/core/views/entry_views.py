from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

from ..models import Author, Entry, Image
from ..forms import EntryForm

def author_owns_profile(request, author):
    #as an author, other authors cannot modify my entries, so that I don't get impersonated.
    if (author.user_id is None or author.user_id != request.user.id) and not request.user.is_staff:
        return False
    return True


@login_required
def create_entry(request, author_serial):
    """HTML view to create a new entry for the given author."""
    author = get_object_or_404(Author, serial=author_serial)

    if not author_owns_profile(request, author):
        return HttpResponseForbidden("You cannot create entries for another author.")

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.author = author
            base_host = author.host.rstrip("/")
            entry.url = f"{base_host}/authors/{author.serial}/entries/{entry.serial}"

            if form.cleaned_data['content_type'] == 'image':
                uploaded_image = form.cleaned_data.get('uploaded_image')
                if uploaded_image:
                    image = Image.objects.create(
                        author=author,
                        image=uploaded_image
                    )
                    entry.image_url = image.url
            else:
                entry.image_url = ""

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
    """HTML view to edit an existing entry by UUID."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=author)
    if entry.visibility == "DELETED":
        return HttpResponseForbidden("You cannot edit a deleted entry.")
    if not author_owns_profile(request, author):
        return HttpResponseForbidden("You cannot edit another author's entries.")

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES, instance=entry)
        if form.is_valid():
            if form.cleaned_data['content_type'] == 'image':
                uploaded_image = form.cleaned_data.get('uploaded_image')
                if uploaded_image:
                    image = Image.objects.create(
                        author=author,
                        image=uploaded_image
                    )
                    form.instance.image_url = image.url
            else:
                form.instance.image_url = ""

            form.save()
            return redirect("author_profile", author_serial=author.serial)
    else:
        form = EntryForm(instance=entry)

    return render(request, "core/entry_form.html", {"author": author, "form": form, "is_edit": True, "entry": entry})


@login_required
def edit_entry_legacy(request, author_serial, entry_id):
    """Backward-compatible HTML edit view that accepts a legacy integer entry id."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, pk=entry_id, author=author)
    return edit_entry(request, author_serial=author.serial, entry_serial=entry.serial)


@login_required
def delete_entry(request, author_serial, entry_serial):
    """HTML view to soft-delete an entry by setting its visibility to DELETED."""
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

def view_entry(request, author_serial, entry_serial):
    """HTML view for a single entry, enforcing visibility and friendship rules."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, serial=entry_serial, author=author)

    if entry.visibility == "DELETED":
        return HttpResponseForbidden("This entry has been deleted.")

    elif entry.visibility == "PUBLIC" or entry.visibility == "UNLISTED":
        return render(request, "core/view_entry.html", {"entry": entry, "author": author})
    
    else:
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You do not have permission to view this entry.")
        
        requestingAuthor = getattr(request.user, "author_profile", None)
        is_owner = request.user.is_staff or requestingAuthor == author
        is_friend = requestingAuthor is not None and author.get_friends().filter(serial=requestingAuthor.serial).exists()

        if is_owner or is_friend:
            return render(request, "core/view_entry.html", {"entry": entry, "author": author})
        
        return HttpResponseForbidden("You do not have permission to view this entry.")

@login_required
def delete_entry_legacy(request, author_serial, entry_id):
    """Backward-compatible HTML delete view that accepts a legacy integer entry id."""
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, pk=entry_id, author=author)
    return delete_entry(request, author_serial=author.serial, entry_serial=entry.serial)