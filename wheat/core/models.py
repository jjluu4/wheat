from django.db import models
from django.utils import timezone

# Core is only responsible for base offline functionality, other models for node and interconnectivity should be in a new app
# -Z

class Author(models.Model):
    url = models.URLField(unique=True)

    host = models.URLField()
    displayName = models.CharField()
    github = models.URLField()
    profileImage = models.URLField()
    web = models.URLField()


class Entry(models.Model):
    url = models.URLField(unique=True)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='entries')

    content = models.TextField()
    content_type = models.CharField(default='text/plain')

    published = models.DateTimeField(default=timezone.now)


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