from django import forms

from .models import Author, Entry


class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["displayName", "description", "github", "profileImage"]


class EntryForm(forms.ModelForm):
    #form for entry
    CONTENT_TYPE_CHOICES = [
        ("text/plain", "Plain text"),
        ("text/markdown", "CommonMark (Markdown)"),
        ("image", "Image (by URL)"),
    ]

    title = forms.CharField(required=False)
    content_type = forms.ChoiceField(choices=CONTENT_TYPE_CHOICES)
    visibility = forms.ChoiceField(
        choices=[
            ("PUBLIC", "Public"),
            ("UNLISTED", "Unlisted"),
            ("FRIENDS", "Friends-only"),
        ]
    )

    class Meta:
        model = Entry
        fields = ["title", "content", "content_type", "image_url", "visibility"]

    def clean(self):
        cleaned = super().clean()
        title = (cleaned.get("title") or "").strip()
        ctype = cleaned.get("content_type")
        image_url = (cleaned.get("image_url") or "").strip()
        content = (cleaned.get("content") or "").strip()

        if ctype == "image" and not image_url:
            self.add_error("image_url", "provide an image url")

        cleaned["title"] = title or getattr(self.instance, "title", "") or "Untitled"
        cleaned["image_url"] = image_url
        cleaned["content"] = content
        return cleaned
