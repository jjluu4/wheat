from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseNotFound
import logging

from ..apis.follow_api import (
    forward_follow_request_to_remote_inbox,
    notify_remote_follow_acceptance,
    notify_remote_follow_rejection,
    notify_remote_unfollow,
)
from ..helpers import author_requires_remote_inbox
from ..models import Author, Follow

logger = logging.getLogger(__name__)

@login_required
def follow_author(request, author_serial):
    """Create or re-request a follow from the current user to the target author."""
    actor = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, serial=author_serial)

    follow = Follow.objects.filter(actor=actor, target=target).first()

    if follow is None or follow.status != "ACCEPTED":
        # Remote follows deliver to another node's inbox; same-node follows stay local.
        delivered, delivery_error = forward_follow_request_to_remote_inbox(actor, target)
        if not delivered:
            
            messages.error(request, delivery_error)
            return redirect("author_profile", author_serial=target.serial)

        if follow is None:
            Follow.objects.create(actor=actor, target=target, status="REQUESTED")
        elif follow.status != "REQUESTED":
            follow.status = "REQUESTED"
            follow.save(update_fields=["status"])
    
    return redirect("author_profile", author_serial=target.serial)

@login_required
def accept_follow(request, author_serial):
    """Accept a pending follow request from the specified author."""
    target = get_object_or_404(Author, user=request.user)
    actor = get_object_or_404(Author, serial=author_serial)

    try:
        follow = Follow.objects.get(
            actor=actor,
            target=target,
            status="REQUESTED"
        )

        follow.status = "ACCEPTED"
        follow.save()
        if author_requires_remote_inbox(actor):
            delivered, delivery_error = notify_remote_follow_acceptance(actor, target)
            

        return redirect("author_profile", author_serial=target.serial)
    
    except Follow.DoesNotExist:
        return HttpResponseNotFound("Follow request cannot be found.")

@login_required
def reject_follow(request, author_serial):
    """Reject a pending follow request from the specified author."""
    target = get_object_or_404(Author, user=request.user)
    actor = get_object_or_404(Author, serial=author_serial)

    try:
        follow = Follow.objects.get(
            actor=actor,
            target=target,
            status="REQUESTED"
        )

        follow.status = "REJECTED"
        follow.save()

        if author_requires_remote_inbox(actor):
            delivered, err = notify_remote_follow_rejection(actor, target)

        return redirect("author_profile", author_serial=target.serial)
    
    except Follow.DoesNotExist:
        return HttpResponseNotFound("Follow request cannot be found.")

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
def unfollow(request, author_serial):
    """Remove a follow relationship (ACCEPTED or REQUESTED) from the current user to the target author."""
    actor = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, serial=author_serial)

    follow = Follow.objects.filter(actor=actor, target=target).first()
    if follow is None:
        return HttpResponseNotFound("Follow request cannot be found.")

    follow.delete()
    if author_requires_remote_inbox(target):
        delivered, err = notify_remote_unfollow(actor, target)
    return redirect("author_profile", author_serial=target.serial)
