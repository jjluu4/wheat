from django.db import models
from django.utils import timezone
from django.db.models import Q, CheckConstraint, UniqueConstraint, F
from django.conf import settings
import uuid

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
    ("REQUESTING", "Requesting"),
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
    displayName = models.CharField(max_length=255)
    github = models.URLField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    profileImage = models.URLField(blank=True, default="https://placehold.co/600x400")
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
    
    @staticmethod
    def get_entries(viewer):
        following = viewer.get_following()
        friends = viewer.get_friends()

        entryFilter = (
            Q(visibility="PUBLIC") | 
            Q(visibility="FRIENDS", author__in=friends) | 
            Q(visibility="UNLISTED", author__in=following)
        )

        return Entry.objects.filter(entryFilter)



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
