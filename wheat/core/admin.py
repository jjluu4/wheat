from django.contrib import admin
from .models import Author, Entry, Comment, EntryLike, CommentLike, Follow, Image, RemoteNode
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

import uuid

from .helpers import build_local_avatar_placeholder_url


admin.site.register(Author)
admin.site.register(Entry)
admin.site.register(Comment)
admin.site.register(EntryLike)
admin.site.register(CommentLike)
admin.site.register(Follow)
admin.site.register(Image)
# Register your models here.


@admin.register(RemoteNode)
class RemoteNodeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "base_url", "api_base_url", "username", "is_active", "updated_at")
    search_fields = ("name", "base_url", "api_base_url", "username")
    list_filter = ("is_active",)
    ordering = ("base_url", "name")

@admin.action(description="Approve new users")
def approve_pending_users(modeladmin, request, queryset):
    for user in queryset:
        if not user.is_active:
            user.is_active = True
            user.save()

            if not hasattr(user, "author_profile"):
                base = request.build_absolute_uri("/").rstrip("/")
                author_serial = uuid.uuid4()

                Author.objects.create(
                    user=user,
                    serial=author_serial,
                    host=f"{base}/api/",
                    url=f"{base}/api/authors/{author_serial}",
                    web=f"{base}/authors/{author_serial}/",
                    displayName=user.username,
                    github=f"https://github.com/{user.username}",
                    description="",
                    profileImage=build_local_avatar_placeholder_url(request),
                )

admin.site.unregister(User)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = [approve_pending_users]
    list_filter = UserAdmin.list_filter + ('is_active',)
