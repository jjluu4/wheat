from django.contrib import admin
from .models import Author, Entry, Comment, Like, Follow, FollowRequest

admin.site.register(Author)
admin.site.register(Entry)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Follow)
admin.site.register(FollowRequest)
# Register your models here.
