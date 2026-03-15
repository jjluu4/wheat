from rest_framework import serializers
from django.db import models
from .models import Author, Entry, Comment, EntryLike, CommentLike
import uuid
from django.utils import timezone

class AuthorSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="author", read_only=True)
    id = serializers.URLField(source="url")

    class Meta:
        model = Author
        fields = ["type", "serial", "id", "host", "displayName", "github", "profileImage", "web"]


class EntrySerializer(serializers.ModelSerializer):
    
    type = serializers.CharField(default="entry", read_only=True)
    id = serializers.URLField(source="url", read_only=True)
    contentType = serializers.CharField(source="content_type")
    imageUrl = serializers.URLField(source="image_url", required=False, allow_blank=True)
    title = serializers.CharField(default="Title", read_only=True)
    description = serializers.CharField(default="Description", read_only=True)
    web = serializers.CharField(default="Webpage", read_only=True)
    published = serializers.DateTimeField(default=timezone.now, read_only=True)

    class Meta:
        model = Entry
        fields = ["type", "title", "id", "web", "description", "contentType", "content", "imageUrl", "author", "published", "visibility"]

    def create(self, validated_data):
        return Entry.objects.create(**validated_data)


class CommentSerializer(serializers.ModelSerializer):
    type=serializers.CharField(default="comment", read_only=True)
    id = serializers.URLField(source="url", read_only=True)
    author=AuthorSerializer(read_only=True)
    entry = serializers.URLField(source='entry.url', read_only=True)
    contentType = serializers.CharField(source="content_type", read_only=True)

    class Meta:
        model=Comment
        fields=['type', 'id', 'url', 'author', 'content', 'contentType', 'published', 'entry']


class EntryLikeSerializer(serializers.ModelSerializer):
    type=serializers.CharField(default="like", read_only=True)
    id = serializers.URLField(source="url", read_only=True)
    author = AuthorSerializer(read_only=True)
    object = serializers.URLField(source="entry.url", read_only=True)

    class Meta:
        model=EntryLike
        fields=['type', 'id', 'author', 'published', 'object']


class CommentLikeSerializer(serializers.ModelSerializer):
    type=serializers.CharField(default="like", read_only=True)
    id = serializers.URLField(source="url", read_only=True)
    author = AuthorSerializer(read_only=True)
    object = serializers.URLField(source="comment.url", read_only=True)

    class Meta:
        model=CommentLike
        fields=['type', 'id', 'author', 'published', 'object']
