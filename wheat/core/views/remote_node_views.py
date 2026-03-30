from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import RemoteNodeForm
from ..helpers import (
    REMOTE_AUTHORS_FETCH_CHUNK_SIZE,
    fetch_remote_authors_page,
    remote_authors_fetch_session_key,
)
from ..models import RemoteNode


def _forbid_non_staff(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to manage remote nodes.")
    return None


@login_required
def remote_node_list(request):
    forbidden = _forbid_non_staff(request)
    if forbidden:
        return forbidden

    nodes = RemoteNode.objects.order_by("base_url", "name")
    return render(request, "core/remote_node_list.html", {"nodes": nodes})


@login_required
def remote_node_add(request):
    forbidden = _forbid_non_staff(request)
    if forbidden:
        return forbidden

    if request.method == "POST":
        form = RemoteNodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("remote_node_list")
    else:
        form = RemoteNodeForm(initial={"is_active": True})

    return render(
        request,
        "core/remote_node_form.html",
        {"form": form, "is_edit": False},
    )


@login_required
def remote_node_edit(request, pk):
    forbidden = _forbid_non_staff(request)
    if forbidden:
        return forbidden

    remote_node = get_object_or_404(RemoteNode, pk=pk)

    if request.method == "POST":
        form = RemoteNodeForm(request.POST, instance=remote_node)
        if form.is_valid():
            form.save()
            return redirect("remote_node_list")
    else:
        form = RemoteNodeForm(instance=remote_node)

    return render(
        request,
        "core/remote_node_form.html",
        {"form": form, "is_edit": True, "remote_node": remote_node},
    )


@login_required
def remote_node_delete(request, pk):
    forbidden = _forbid_non_staff(request)
    if forbidden:
        return forbidden

    remote_node = get_object_or_404(RemoteNode, pk=pk)

    if request.method == "POST":
        remote_node.delete()
        return redirect("remote_node_list")

    return render(
        request,
        "core/remote_node_confirm_delete.html",
        {"remote_node": remote_node},
    )


@login_required
@require_POST
def remote_node_toggle(request, pk):
    forbidden = _forbid_non_staff(request)
    if forbidden:
        return forbidden

    remote_node = get_object_or_404(RemoteNode, pk=pk)
    target_state = request.POST.get("target_state")
    if target_state == "enable":
        desired_active = True
    elif target_state == "disable":
        desired_active = False
    else:
        messages.error(request, "Invalid remote node toggle request.")
        return redirect("remote_node_list")

    if remote_node.is_active != desired_active:
        remote_node.is_active = desired_active
        remote_node.save(update_fields=["is_active"])
    return redirect("remote_node_list")


@login_required
@require_POST
def fetch_remote_node_authors_page(request, pk):
    """
    Staff: fetch the *next* chunk (5 authors) from this remote node's paginated
    GET /api/authors. Page cursor is stored in the session per node so each click
    advances (Zane: first 5, then more when the user requests it).
    """
    forbidden = _forbid_non_staff(request)
    if forbidden:
        return forbidden

    node = get_object_or_404(RemoteNode, pk=pk, is_active=True)
    sk = remote_authors_fetch_session_key(node.pk)
    try:
        page = int(request.session.get(sk, 1))
    except (TypeError, ValueError):
        page = 1
    page = max(1, page)

    result = fetch_remote_authors_page(node, page, REMOTE_AUTHORS_FETCH_CHUNK_SIZE)
    if result["error"]:
        messages.error(request, result["error"])
    else:
        label = node.name or node.base_url
        if result["item_count"] == 0:
            request.session[sk] = 1
            messages.info(
                request,
                f"No authors returned from {label} (page {page}). Cursor reset to start.",
            )
        elif result["has_more"]:
            request.session[sk] = page + 1
            messages.success(
                request,
                f"Fetched up to {REMOTE_AUTHORS_FETCH_CHUNK_SIZE} from {label} (remote page {page}): "
                f"stored or updated {result['upserted']} author(s). Click again for the next batch.",
            )
        else:
            request.session[sk] = 1
            messages.success(
                request,
                f"Fetched last batch from {label} (remote page {page}): "
                f"stored or updated {result['upserted']} author(s). End of list — next click starts from page 1 again.",
            )
        request.session.modified = True
    return redirect("author_list")
