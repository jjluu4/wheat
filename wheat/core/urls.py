from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path("accounts/signup/", views.signup, name="signup"),

    path("authors/", views.author_list, name="author_list"),

    path("authors/me/", views.my_profile, name="my_profile"),

    # stable UUID serial routes
    path("authors/<uuid:author_serial>/", views.author_profile, name="author_profile"),
    path("authors/<uuid:author_serial>/edit/", views.author_edit, name="author_edit"),
]