from django.db import models
from django.utils import timezone
from django.db.models import Q, CheckConstraint, UniqueConstraint, F
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid
import urllib.parse

# Core is only responsible for base offline functionality, other models for node and interconnectivity should be in a new app
# -Z

VISIBILITIES = [
    ("PUBLIC", "Public"),
    ("UNLISTED", "Unlisted"),
    ("FRIENDS", "Friends"),
    ("DELETED", "Deleted"),
]

FOLLOW_STATUSES = [
    ("ACCEPTED", "Accepted"),
    ("REQUESTED", "Requested"),
    ("REJECTED", "Rejected")
]

class Author(models.Model):
    # Link Django User -> Author (so each login can own exactly one author profile)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="author_profile",
    )

    # Stable identity that does NOT depend on DB pk
    serial = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    url = models.URLField(unique=True)
    host = models.URLField()
    displayName = models.CharField(max_length=32)
    github = models.URLField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    profileImage = models.URLField(blank=True, default="")
    web = models.URLField(blank=True, default="")

    def get_followers(self):
        return Author.objects.filter(following__target=self, following__status="ACCEPTED")

    def get_following(self):
        return Author.objects.filter(followers__actor=self, followers__status="ACCEPTED")

    def get_friends(self):
        return Author.objects.filter(following__target=self, following__status="ACCEPTED", followers__actor=self, followers__status="ACCEPTED")

    def __str__(self):
        return self.displayName



class Entry(models.Model):
    url = models.URLField(unique=True)
    
    serial = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='entries')
    title = models.CharField(max_length=255, default="Untitled")
    content = models.TextField(blank=True, default="")
    content_type = models.CharField(max_length=100, default='text/plain')
    
    image_url = models.URLField(blank=True, default="")
    published = models.DateTimeField(default=timezone.now)
    visibility = models.CharField(max_length=10, choices=VISIBILITIES, default="PUBLIC")
    web = models.URLField(blank=True, default="")
    
    @staticmethod
    def get_entries(viewer):
        following = viewer.get_following()
        friends = viewer.get_friends()

        entryFilter = (
            Q(visibility="PUBLIC") | 
            Q(visibility="FRIENDS", author__in=friends) | 
            Q(visibility="UNLISTED", author__in=following) |
            Q(author=viewer)
        )
        qs = Entry.objects.filter(entryFilter)
        viewer_is_admin = getattr(getattr(viewer, "user", None), "is_staff", False)
        if not viewer_is_admin:
            qs = qs.exclude(visibility="DELETED")

        return qs



class Comment(models.Model):
    url = models.URLField(unique=True)
    serial = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='comments_made')
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='comments')

    content_type = models.CharField(max_length=100, default='text/plain')
    content = models.TextField()

    published = models.DateTimeField(default=timezone.now)


class EntryLike(models.Model):
    serial = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    url = models.URLField(unique=True)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='liked_entries')
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='likes')

    published = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            UniqueConstraint(
                name="unique_entry_like",
                fields=["author", "entry"],
            )
        ]

class CommentLike(models.Model):
    serial = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    url = models.URLField(unique=True)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='liked_comments')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')

    published = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            UniqueConstraint(
                name="unique_comment_like",
                fields=["author", "comment"],
            )
        ]


class Follow(models.Model):
    actor = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='following')
    target = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='followers')
    status = models.CharField(choices=FOLLOW_STATUSES, default="REQUESTED")

    class Meta:
        constraints = [
            # Ensure an author cannot follow themselves.
            CheckConstraint(
                name="restrict_self_follow",
                condition=~Q(actor=F("target"))
            ),

            # Only one follow object can exist per actor to target.
            UniqueConstraint(
                name="unique_follow",
                fields=["actor", "target"]
            )
        ]

def get_image_upload_path(instance, filename):
    ext=filename.split('.')[-1].lower()
    if ext not in ['jpg', 'png']:
        ext='jpg'
    return f"{instance.serial}.{ext}"

class Image(models.Model):
    serial = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    image = models.ImageField(upload_to=get_image_upload_path)
    url = models.URLField(unique=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='images')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.url:
            base_host = self.author.host.rstrip("/")
            ext = self.image.name.split('.')[-1] if self.image else 'jpg'
            self.url = f"/media/{self.serial}.{ext}"
            super().save(update_fields=['url'])


class RemoteNode(models.Model):
    name = models.CharField(max_length=255, blank=True, default="")
    base_url = models.URLField(unique=True)
    api_base_url = models.URLField(blank=True, default="")
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or self.base_url

    @staticmethod
    def _normalize_url(value):
        value = (value or "").strip()
        if not value:
            return ""
        return value.rstrip("/")

    def clean(self):
        super().clean()

        self.name = (self.name or "").strip()
        self.base_url = self._normalize_url(self.base_url)
        self.api_base_url = self._normalize_url(self.api_base_url)
        self.username = (self.username or "").strip()
        self.notes = (self.notes or "").strip()

        if self.base_url and not self.api_base_url:
            self.api_base_url = f"{self.base_url}/api"

        if self.api_base_url:
            parts = urllib.parse.urlsplit(self.api_base_url)
            api_path = (parts.path or "").strip().rstrip("/")
            if not api_path:
                self.api_base_url = self._normalize_url(f"{parts.scheme}://{parts.netloc}/api")

        duplicate_qs = RemoteNode.objects.filter(base_url=self.base_url)
        if self.pk:
            duplicate_qs = duplicate_qs.exclude(pk=self.pk)
        if self.base_url and duplicate_qs.exists():
            raise ValidationError({"base_url": "A remote node with this base URL already exists."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class InboxItem(models.Model):
    owner = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="inbox_items")
    item_type = models.CharField(max_length=20)
    item_id = models.URLField()
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                name="unique_inbox_item_per_owner",
                fields=["owner", "item_id"],
            )
        ]
