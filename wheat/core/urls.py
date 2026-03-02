from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/logged_out", views.logged_out, name="logged_out"),

    path("authors/", views.author_list, name="author_list"),

    path("authors/me/", views.my_profile, name="my_profile"),
    
    path("stream/", views.my_stream, name="my_stream"),

    # stable UUID serial routes
    path("authors/<uuid:author_serial>/", views.author_profile, name="author_profile"),
    path("authors/<uuid:author_serial>/edit/", views.author_edit, name="author_edit"),
    path("authors/<uuid:author_serial>/entries/new/", views.create_entry, name="entry_create"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/edit/", views.edit_entry_legacy, name="entry_edit"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/delete/",views.delete_entry_legacy, name="entry_delete"),
    path("authors/<uuid:author_serial>/follow/", views.follow_author, name="follow_author"),
    path("authors/<uuid:author_serial>/accept/", views.accept_follow, name="accept_follow"),
    path("authors/<uuid:author_serial>/reject/", views.reject_follow, name="reject_follow"),
    path("authors/<uuid:author_serial>/unfollow/", views.unfollow, name="unfollow_author"),
    path("authors/<uuid:author_serial>/requests/", views.follow_requests, name="follow_requests"),
    path("authors/<uuid:author_serial>/followers/", views.followers, name="followers_list"),
    path("authors/<uuid:author_serial>/following/", views.following, name="following_list"),

    # API endpoints
    path("api/authors/<uuid:author_serial>/", views.single_author, name="api_single_author"),
    path("api/authors", views.all_authors, name="api_all_authors"),

    # Canonical stable routes use entry serial (UUID), not DB pk
    path("authors/<uuid:author_serial>/entries/<uuid:entry_serial>/edit/", views.edit_entry, name="entry_edit"),
    path("authors/<uuid:author_serial>/entries/<uuid:entry_serial>/delete/", views.delete_entry, name="entry_delete"),

    # Backward-compatible legacy routes
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/edit/", views.edit_entry_legacy, name="entry_edit_legacy"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/delete/", views.delete_entry_legacy, name="entry_delete_legacy"),
]
