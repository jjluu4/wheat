import uuid

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden

from ..helpers import (
    REMOTE_AUTHORS_FETCH_CHUNK_SIZE,
    authors_native_to_this_node_qs,
    build_local_avatar_placeholder_url,
    fetch_remote_authors_catalog_page,
    normalize_url,
    resolved_remote_api_base,
    resolve_remote_author,
)
from ..models import Author, Entry, Follow, RemoteNode
from ..permissions import get_requesting_author
from ..github import fetch_public_events
from ..github_to_entries import save_event_as_entry

def _catalog_query_url(request, *, local_page=None, remote_pk=None, remote_page=None):
    """Preserve existing lp / r{pk} params; override one slice of catalog state."""
    q = request.GET.copy()
    if local_page is not None:
        if local_page <= 1:
            q.pop("lp", None)
        else:
            q["lp"] = str(local_page)
    if remote_pk is not None and remote_page is not None:
        key = f"r{remote_pk}"
        if remote_page <= 1:
            q.pop(key, None)
        else:
            q[key] = str(remote_page)
    encoded = q.urlencode()
    return f"?{encoded}" if encoded else ""


def _local_api_base(request):
    return request.build_absolute_uri("/").rstrip("/")


def open_remote_author(request):
    """
    Resolve a remote author FQID (from the catalog) into a local Author row and redirect
    to our author_profile. Avoids linking straight to item.web, which would leave this node
    and break the logged-in Follow flow.
    """
    fqid = (request.GET.get("fqid") or "").strip()
    if not fqid:
        return HttpResponseBadRequest("Missing fqid query parameter.")

    author = resolve_remote_author(fqid)
    if author is None:
        raise Http404("Could not resolve that author.")

    return redirect("author_profile", author_serial=author.serial)


def author_list(request):
    """
    Authors browser: one section for this node (native authors only, same filter as GET /api/authors/)
    and one section per active RemoteNode (live GET to that node's /api/authors, no upsert).
    Pagination: query lp= for local, r{node_pk}= for each remote. Size is fixed (5).
    """
    size = REMOTE_AUTHORS_FETCH_CHUNK_SIZE

    raw_lp = request.GET.get("lp", "1")
    try:
        local_page = max(1, int(raw_lp))
    except (TypeError, ValueError):
        local_page = 1

    local_qs = authors_native_to_this_node_qs(request)
    local_paginator = Paginator(local_qs, size)
    local_obj = local_paginator.get_page(local_page)

    author_sections = [
        {
            "kind": "local",
            "label": "This node",
            "subtitle": normalize_url(_local_api_base(request) + "/api"),
            "page_obj": local_obj,
            "prev_url": _catalog_query_url(request, local_page=local_obj.previous_page_number())
            if local_obj.has_previous()
            else None,
            "next_url": _catalog_query_url(request, local_page=local_obj.next_page_number())
            if local_obj.has_next()
            else None,
            "first_url": _catalog_query_url(request, local_page=1) if local_obj.number > 1 else None,
            "last_url": _catalog_query_url(request, local_page=local_paginator.num_pages)
            if local_obj.number < local_paginator.num_pages
            else None,
            "error": None,
        }
    ]

    if request.user.is_authenticated:
        for node in RemoteNode.objects.filter(is_active=True).order_by("base_url", "name"):
            key = f"r{node.pk}"
            raw_rp = request.GET.get(key, "1")
            try:
                rpage = max(1, int(raw_rp))
            except (TypeError, ValueError):
                rpage = 1

            cat = fetch_remote_authors_catalog_page(node, rpage, size)
            label = node.name or node.base_url

            num_pages = cat["num_pages"]
            has_prev = rpage > 1
            has_next = cat["has_next"]

            author_sections.append(
                {
                    "kind": "remote",
                    "label": label,
                    "subtitle": resolved_remote_api_base(node),
                    "items": cat["authors"],
                    "page": rpage,
                    "total_count": cat["total_count"],
                    "num_pages": num_pages,
                    "prev_url": _catalog_query_url(request, remote_pk=node.pk, remote_page=rpage - 1)
                    if has_prev
                    else None,
                    "next_url": _catalog_query_url(request, remote_pk=node.pk, remote_page=rpage + 1)
                    if has_next
                    else None,
                    "first_url": _catalog_query_url(request, remote_pk=node.pk, remote_page=1)
                    if rpage > 1
                    else None,
                    "last_url": _catalog_query_url(request, remote_pk=node.pk, remote_page=num_pages)
                    if num_pages is not None and rpage < num_pages
                    else None,
                    "error": cat["error"],
                }
            )

    return render(
        request,
        "core/author_list.html",
        {
            "author_sections": author_sections,
            "authors_list_page_size": size,
        },
    )


def author_profile(request, author_serial):
    """Show an author's profile page and their visible entries."""
    author = get_object_or_404(Author, serial=author_serial)
    requesting_author = get_requesting_author(request)

    # Auto-import newest GitHub events as PUBLIC entries
    # (should not duplicate if save_event_as_entry uses unique URL)
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
        entries_heading = "Your Entries" if author.user_id == request.user.id else "Visible Entries"
    elif requesting_author:
        entries = Entry.get_entries(requesting_author).filter(author=author)
        entries_heading = "Visible Entries"
    else:
        entries = Entry.objects.filter(author=author, visibility="PUBLIC")
        entries_heading = "Public Entries"

    entries = entries.order_by("-published")

    followStatus = None
    if requesting_author and requesting_author != author:
        follow = Follow.objects.filter(
            actor=requesting_author,
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
            "entries_heading": entries_heading,
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
            profileImage=build_local_avatar_placeholder_url(request),
        )

    return redirect("author_profile", author_serial=author.serial)
