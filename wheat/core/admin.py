from django.contrib import admin
from .models import Author, Entry, Comment, Like, Follow
admin.site.register(Author)
admin.site.register(Entry)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Follow)
# Register your models here.
