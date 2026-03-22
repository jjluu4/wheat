from django.contrib import admin
from .models import Author, Entry, Comment, EntryLike, CommentLike, Follow, Image
admin.site.register(Author)
admin.site.register(Entry)
admin.site.register(Comment)
admin.site.register(EntryLike)
admin.site.register(CommentLike)
admin.site.register(Follow)
admin.site.register(Image)
# Register your models here.
