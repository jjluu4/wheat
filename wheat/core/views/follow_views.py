from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
import logging

from ..apis.follow_api import (
    ensure_follow_requested,
    forward_follow_request_to_remote_inbox,
    revert_follow_requested_transition,
    notify_remote_follow_acceptance,
    notify_remote_follow_rejection,
    notify_remote_unfollow,
)
from ..helpers import author_requires_remote_inbox
from ..models import Author, Follow

logger = logging.getLogger(__name__)

@login_required
@require_POST
def follow_author(request, author_serial):
    """Create or re-request a follow from the current user to the target author."""
    actor = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, serial=author_serial)

    follow, state_changed, previous_status = ensure_follow_requested(actor, target)
    if state_changed:
        delivered, delivery_error = forward_follow_request_to_remote_inbox(actor, target)
        if not delivered:
            revert_follow_requested_transition(follow, previous_status)
            messages.error(request, delivery_error)
            return redirect("author_profile", author_serial=target.serial)
    
    return redirect("author_profile", author_serial=target.serial)

@login_required
@require_POST
def accept_follow(request, author_serial):
    """Accept a pending follow request from the specified author."""
    target = get_object_or_404(Author, user=request.user)
    actor = get_object_or_404(Author, serial=author_serial)

    follow = Follow.objects.filter(actor=actor, target=target).first()
    if follow is None:
        messages.info(request, "Follow request cannot be found.")
        return redirect("author_profile", author_serial=target.serial)
    if follow.status == "ACCEPTED":
        messages.info(request, "Follow request is already accepted.")
        return redirect("author_profile", author_serial=target.serial)
    if follow.status != "REQUESTED":
        messages.info(request, "Follow request is not pending.")
        return redirect("author_profile", author_serial=target.serial)

    follow.status = "ACCEPTED"
    follow.save(update_fields=["status"])
    if author_requires_remote_inbox(actor):
        notify_remote_follow_acceptance(actor, target)

    return redirect("author_profile", author_serial=target.serial)

@login_required
@require_POST
def reject_follow(request, author_serial):
    """Reject a pending follow request from the specified author."""
    target = get_object_or_404(Author, user=request.user)
    actor = get_object_or_404(Author, serial=author_serial)
    follow = Follow.objects.filter(actor=actor, target=target).first()
    if follow is None:
        messages.info(request, "Follow request cannot be found.")
        return redirect("author_profile", author_serial=target.serial)
    if follow.status == "REJECTED":
        messages.info(request, "Follow request is already rejected.")
        return redirect("author_profile", author_serial=target.serial)
    if follow.status != "REQUESTED":
        messages.info(request, "Follow request is not pending.")
        return redirect("author_profile", author_serial=target.serial)

    follow.status = "REJECTED"
    follow.save(update_fields=["status"])

    if author_requires_remote_inbox(actor):
        notify_remote_follow_rejection(actor, target)

    return redirect("author_profile", author_serial=target.serial)

@login_required
def follow_requests(request, author_serial):
    """HTML view listing pending follow requests for the current user."""
    target = get_object_or_404(Author, user=request.user)

    requestList = Follow.objects.filter(
        target=target,
        status="REQUESTED"
    ).select_related("actor").order_by("actor__displayName", "actor__url")

    return render(request, "core/follow_requests.html", {"requests": requestList, "author": target})

@login_required
def following(request, author_serial):
    """HTML view listing authors the current user is following."""
    author = get_object_or_404(Author, user=request.user)

    followingQuery = Follow.objects.filter(
        actor=author,
        status__in=["REQUESTED", "ACCEPTED"]
    ).select_related("target").order_by("target__displayName", "target__url")

    followingList = []
    for q in followingQuery:
        followingList.append(q.target)

    return render(request, "core/follow_list.html", {"authors": followingList, "follow_type": "Following", "author": author})

@login_required
def followers(request, author_serial):
    """HTML view listing authors who follow the current user."""
    author = get_object_or_404(Author, user=request.user)

    followerQuery = Follow.objects.filter(
        target=author,
        status="ACCEPTED"
    ).select_related("actor").order_by("actor__displayName", "actor__url")

    followerList = []
    for q in followerQuery:
        followerList.append(q.actor)

    return render(request, "core/follow_list.html", {"authors": followerList, "follow_type": "Followers", "author": author})

@login_required
@require_POST
def unfollow(request, author_serial):
    """Remove a follow relationship (ACCEPTED or REQUESTED) from the current user to the target author."""
    actor = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, serial=author_serial)

    follow = Follow.objects.filter(actor=actor, target=target).first()
    if follow is None:
        messages.info(request, "Follow request cannot be found.")
        return redirect("author_profile", author_serial=target.serial)

    follow.delete()
    if author_requires_remote_inbox(target):
        notify_remote_unfollow(actor, target)
    return redirect("author_profile", author_serial=target.serial)
