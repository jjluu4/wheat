from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..federation import sync_remote_authors_and_public_entries
from ..forms import RemoteNodeForm
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
    remote_node.is_active = not remote_node.is_active
    remote_node.save()
    return redirect("remote_node_list")


@login_required
@require_POST
def remote_node_sync(request):
    forbidden = _forbid_non_staff(request)
    if forbidden:
        return forbidden

    result = sync_remote_authors_and_public_entries()
    messages.success(
        request,
        f"Sync complete: imported/updated {result['authors']} authors and {result['entries']} entries.",
    )
    return redirect("remote_node_list")
