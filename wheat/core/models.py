from django.db import models
from django.utils import timezone
from django.db.models import Q
import uuid

# Core is only responsible for base offline functionality, other models for node and interconnectivity should be in a new app
# -Z

VISIBILITIES = [
    ("PUBLIC", "Public"),
    ("UNLISTED", "Unlisted"),
    ("FRIENDS", "Friends"),
    ("DELETED", "Deleted"),
]

class Author(models.Model):
    # Stable identity that does NOT depend on DB pk
    serial = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    url = models.URLField(unique=True)
    host = models.URLField()
    displayName = models.CharField(max_length=255)
    github = models.URLField()
    description = models.TextField(blank=True, default="")
    profileImage = models.URLField()
    web = models.URLField()

    def get_followers(self):
        return Author.objects.filter(following__target=self)

    def get_following(self):
        return Author.objects.filter(followers__actor=self)

    def get_friends(self):
        return Author.objects.filter(following__target=self, followers__actor=self)

    def __str__(self):
        return self.displayName



class Entry(models.Model):
    url = models.URLField(unique=True)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='entries')

    content = models.TextField()
    content_type = models.CharField(max_length=100, default='text/plain')

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

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='comments_made')
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='comments')

    content = models.TextField()
    published = models.DateTimeField(default=timezone.now)


class Like(models.Model):
    url = models.URLField(unique=True)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='likes')
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='likes')

    published = models.DateTimeField(default=timezone.now)


class Follow(models.Model):
    actor = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='following')
    target = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='followers')


class FollowRequest(models.Model):
    actor = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='outgoing_follow_requests')
    target = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='incoming_follow_requests')

    summary = models.TextField()