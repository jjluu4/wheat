import base64
import uuid

from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Author, Comment, CommentLike, Entry, EntryLike, Follow, InboxItem, RemoteNode


def make_basic_auth_value(username, password):
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def make_basic_auth_headers(username, password):
    return {"HTTP_AUTHORIZATION": make_basic_auth_value(username, password)}


def make_user(username=None, password="pass12345", **overrides):
    username = username or f"user-{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(username=username, password=password, **overrides)


def make_author(
    *,
    user=None,
    display_name="Author",
    serial=None,
    url=None,
    host="http://testserver/api/",
    web=None,
    github="",
    profile_image="",
    description="",
    **extra,
):
    serial = serial or uuid.uuid4()
    url = url or f"{host.rstrip('/')}/authors/{serial}"
    web = web or f"http://testserver/authors/{serial}/"
    return Author.objects.create(
        user=user,
        displayName=display_name,
        serial=serial,
        url=url,
        host=host,
        web=web,
        github=github,
        profileImage=profile_image,
        description=description,
        **extra,
    )


def make_local_author(username=None, password="pass12345", display_name=None, **author_overrides):
    user = make_user(username=username, password=password)
    display_name = display_name or username or user.username
    author = make_author(user=user, display_name=display_name, **author_overrides)
    return user, author


def make_remote_node(
    *,
    name="Remote Node",
    base_url="http://remote-node.example.com",
    api_base_url=None,
    username="remote_user",
    password="remote_pass",
    is_active=True,
    notes="",
    **extra,
):
    api_base_url = api_base_url or f"{base_url.rstrip('/')}/api"
    return RemoteNode.objects.create(
        name=name,
        base_url=base_url,
        api_base_url=api_base_url,
        username=username,
        password=password,
        is_active=is_active,
        notes=notes,
        **extra,
    )


def make_entry(
    *,
    author,
    title="Untitled",
    content="body",
    content_type="text/plain",
    visibility="PUBLIC",
    url=None,
    image_url="",
    web="",
    published=None,
    **extra,
):
    entry_serial = extra.pop("serial", None) or uuid.uuid4()
    url = url or f"http://testserver/api/authors/{author.serial}/entries/{entry_serial}"
    published = published or timezone.now()
    return Entry.objects.create(
        author=author,
        serial=entry_serial,
        url=url,
        title=title,
        content=content,
        content_type=content_type,
        visibility=visibility,
        image_url=image_url,
        web=web,
        published=published,
        **extra,
    )


def make_comment(
    *,
    author,
    entry,
    content="comment body",
    content_type="text/plain",
    url=None,
    published=None,
    **extra,
):
    comment_serial = extra.pop("serial", None) or uuid.uuid4()
    url = url or f"http://testserver/api/authors/{author.serial}/commented/{comment_serial}/"
    published = published or timezone.now()
    return Comment.objects.create(
        author=author,
        entry=entry,
        serial=comment_serial,
        url=url,
        content=content,
        content_type=content_type,
        published=published,
        **extra,
    )


def make_entry_like(*, author, entry, url=None, published=None, **extra):
    like_serial = extra.pop("serial", None) or uuid.uuid4()
    url = url or f"http://testserver/api/authors/{author.serial}/liked/{like_serial}/"
    published = published or timezone.now()
    return EntryLike.objects.create(
        author=author,
        entry=entry,
        serial=like_serial,
        url=url,
        published=published,
        **extra,
    )


def make_comment_like(*, author, comment, url=None, published=None, **extra):
    like_serial = extra.pop("serial", None) or uuid.uuid4()
    url = url or f"http://testserver/api/authors/{author.serial}/liked/{like_serial}/"
    published = published or timezone.now()
    return CommentLike.objects.create(
        author=author,
        comment=comment,
        serial=like_serial,
        url=url,
        published=published,
        **extra,
    )


def make_follow(*, actor, target, status="REQUESTED", **extra):
    return Follow.objects.create(actor=actor, target=target, status=status, **extra)


def make_inbox_item(*, owner, item_type="entry", item_id=None, payload=None, **extra):
    item_id = item_id or f"https://inbox.local/events/{item_type}/{uuid.uuid4()}"
    return InboxItem.objects.create(
        owner=owner,
        item_type=item_type,
        item_id=item_id,
        payload=payload or {},
        **extra,
    )


def build_author_payload(author, **overrides):
    payload = {
        "type": "author",
        "id": author.url,
        "host": author.host,
        "displayName": author.displayName,
        "github": author.github,
        "profileImage": author.profileImage,
        "web": author.web,
    }
    payload.update(overrides)
    return payload


def build_entry_payload(entry, **overrides):
    payload = {
        "type": "entry",
        "title": entry.title,
        "id": entry.url,
        "web": entry.web,
        "description": (entry.content or "")[:200],
        "contentType": entry.content_type,
        "content": entry.content,
        "imageUrl": entry.image_url,
        "author": build_author_payload(entry.author),
        "published": entry.published.isoformat().replace("+00:00", "Z"),
        "visibility": entry.visibility,
    }
    payload.update(overrides)
    return payload


def build_comment_payload(comment, **overrides):
    payload = {
        "type": "comment",
        "id": comment.url,
        "url": comment.url,
        "author": build_author_payload(comment.author),
        "comment": comment.content,
        "content": comment.content,
        "contentType": comment.content_type,
        "published": comment.published.isoformat().replace("+00:00", "Z"),
        "entry": comment.entry.url,
    }
    payload.update(overrides)
    return payload


def build_like_payload(like, *, object_url=None, **overrides):
    if isinstance(like, EntryLike):
        object_url = object_url or like.entry.url
    elif isinstance(like, CommentLike):
        object_url = object_url or like.comment.url

    payload = {
        "type": "like",
        "id": like.url,
        "author": build_author_payload(like.author),
        "published": like.published.isoformat().replace("+00:00", "Z"),
        "object": object_url,
    }
    payload.update(overrides)
    return payload
