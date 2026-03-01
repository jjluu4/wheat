from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    # stable Author.serial (UUID) in URLs
    path("authors/<uuid:author_serial>/", views.author_profile, name="author_profile"),
    path("authors/<uuid:author_serial>/edit/", views.author_edit, name="author_edit"),

    path("authors/", views.author_list, name="author_list"),
]