from django import forms
from .models import Author

class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["displayName", "description", "github", "profileImage"]