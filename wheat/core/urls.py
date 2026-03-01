from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("authors/<int:author_id>/", views.author_profile, name="author_profile"),
    path("authors/<int:author_id>/edit/", views.author_edit, name="author_edit"),
]