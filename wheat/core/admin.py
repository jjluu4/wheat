from django.contrib import admin
from .models import Author, Entry, Comment, EntryLike, CommentLike, Follow
admin.site.register(Author)
admin.site.register(Entry)
admin.site.register(Comment)
admin.site.register(EntryLike)
admin.site.register(CommentLike)
admin.site.register(Follow)
# Register your models here.
