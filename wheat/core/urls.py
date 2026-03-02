from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path("accounts/signup/", views.signup, name="signup"),

    path("authors/", views.author_list, name="author_list"),

    path("authors/me/", views.my_profile, name="my_profile"),
    
    path("stream/", views.my_stream, name="my_stream"),

    # stable UUID serial routes
    path("authors/<uuid:author_serial>/", views.author_profile, name="author_profile"),
    path("authors/<uuid:author_serial>/edit/", views.author_edit, name="author_edit"),
    path("authors/<uuid:author_serial>/entries/new/", views.create_entry, name="entry_create"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/edit/", views.edit_entry, name="entry_edit"),
    path("authors/<uuid:author_serial>/entries/<int:entry_id>/delete/",views.delete_entry, name="entry_delete"),
]