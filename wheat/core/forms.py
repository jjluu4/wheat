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
        ("image", "Image (Upload)"),
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

    uploaded_image = forms.ImageField(
        required=False,
        label="Upload Image",
        help_text="Upload an image for image entries"
    )

    class Meta:
        model = Entry
        fields = ["title", "content", "content_type", "image_url", "visibility"]

    def clean(self):
        cleaned = super().clean()
        title = (cleaned.get("title") or "").strip()
        ctype = cleaned.get("content_type")
        uploaded_image = cleaned.get("uploaded_image")
        content = (cleaned.get("content") or "").strip()

        if ctype == "image" and not uploaded_image:
            self.add_error("uploaded_image", "Please upload an image or change entry type")

        cleaned["title"] = title or getattr(self.instance, "title", "") or "Untitled"
        cleaned["uploaded_image"] = uploaded_image
        cleaned["content"] = content
        return cleaned
