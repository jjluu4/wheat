from rest_framework import serializers
from django.db import models
from .models import Author, Entry
import uuid
from django.utils import timezone

class AuthorSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='author', read_only=True)
    id = serializers.URLField(source='url')

    class Meta:
        model = Author
        fields = ['type', 'id', 'host', 'displayName', 'github', 'profileImage', 'web']

class EntrySerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='entry', read_only=True)
    id = serializers.URLField(source='url')
    title = serializers.CharField(default='Title', read_only=True)
    description = serializers.CharField(default='Desc', read_only=True)
    published = serializers.DateTimeField(default=timezone.now, read_only=True)
    web = serializers.CharField(default='Web', read_only=True)
    
    class Meta:
        model = Entry
        fields = ['type', 'title', 'id', 'web', 'description', 'content_type', 'content', 'author', 'published', 'visibility']
        extra_kwargs = {'id': {'write_only': True}}