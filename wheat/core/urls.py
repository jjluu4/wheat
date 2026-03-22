from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import author_views, entry_views, follow_views, stream_views, authentication_views, views
from .apis import author_api, comment_api, entry_api, follow_api, like_api

urlpatterns = [
    path("", views.index, name="index"),

    path("accounts/signup/", authentication_views.signup, name="signup"),
    path("accounts/logged_out", authentication_views.logged_out, name="logged_out"),

    path("authors/", author_views.author_list, name="author_list"),

    path("authors/me/", author_views.my_profile, name="my_profile"),
    
    path("stream/", stream_views.my_stream, name="my_stream"),

    # stable UUID serial routes
    path("authors/<uuid:author_serial>/", author_views.author_profile, name="author_profile"),
    path("authors/<uuid:author_serial>/edit/", author_views.author_edit, name="author_edit"),
    path("authors/<uuid:author_serial>/entries/new/", entry_views.create_entry, name="entry_create"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/edit/", entry_views.edit_entry_legacy, name="entry_edit"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/delete/",entry_views.delete_entry_legacy, name="entry_delete"),
    path("authors/<uuid:author_serial>/follow/", follow_views.follow_author, name="follow_author"),
    path("authors/<uuid:author_serial>/accept/", follow_views.accept_follow, name="accept_follow"),
    path("authors/<uuid:author_serial>/reject/", follow_views.reject_follow, name="reject_follow"),
    path("authors/<uuid:author_serial>/unfollow/", follow_views.unfollow, name="unfollow_author"),
    path("authors/<uuid:author_serial>/requests/", follow_views.follow_requests, name="follow_requests"),
    path("authors/<uuid:author_serial>/followers/", follow_views.followers, name="followers_list"),
    path("authors/<uuid:author_serial>/following/", follow_views.following, name="following_list"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/", entry_views.view_entry, name="view_entry"),

    # API endpoints
    path("api/authors/<uuid:author_serial>/", author_api.single_author, name="api_single_author"),
    path("api/authors", author_api.all_authors, name="api_all_authors"),
    path("api/authors/<uuid:author_serial>/entries/", entry_api.author_entries, name="api_author_entries"),
    path("api/authors/<uuid:author_serial>/entries/<uuid:entry_serial>/", entry_api.single_entry, name="api_single_entry"),    
    path("api/authors/<uuid:author_serial>/follow_requests", follow_api.get_follow_requests_api, name="api_follow_requests"),
    path("api/authors/<uuid:author_serial>/following", follow_api.get_following_api, name="api_get_following"),
    path('api/authors/<uuid:author_serial>/commented/', comment_api.author_commented, name='api_author_comments'),
    path('api/authors/<uuid:author_serial>/commented/<uuid:comment_serial>/', comment_api.author_commented_single, name='api_author_comments_single'),
    path('api/authors/<uuid:author_serial>/entries/<uuid:entry_serial>/comments/', comment_api.entry_comments, name='api_entry_comments'),
    path('api/authors/<uuid:author_serial>/liked/', like_api.author_liked, name='api_author_liked'),
    path('api/authors/<uuid:author_serial>/entries/<uuid:entry_serial>/likes/', like_api.entry_likes, name='api_entry_likes'),
    path('api/authors/<uuid:author_serial>/entries/<uuid:entry_serial>/comments/<uuid:comment_serial>/likes/', like_api.comment_likes, name='api_comment_likes'),


    # Canonical stable routes use entry serial (UUID), not DB pk
    path("authors/<uuid:author_serial>/entries/<uuid:entry_serial>/edit/", entry_views.edit_entry, name="entry_edit"),
    path("authors/<uuid:author_serial>/entries/<uuid:entry_serial>/delete/", entry_views.delete_entry, name="entry_delete"),
    path("authors/<uuid:author_serial>/entries/<uuid:entry_serial>/", entry_views.view_entry, name="view_entry"),

    # Backward-compatible legacy routes
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/edit/", entry_views.edit_entry_legacy, name="entry_edit_legacy"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/delete/", entry_views.delete_entry_legacy, name="entry_delete_legacy"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
