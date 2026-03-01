from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.urls import reverse
from .models import Author, Entry

# Tests here are mostly for APIs probably for pt1
class AuthorProfilePageTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            url="http://testserver/api/authors/test-author",
            host="http://testserver/api/",
            displayName="Skar",
            github="https://github.com/example",
            description="Hello! This is my profile.",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/1",
        )

        Entry.objects.create(
            url="http://testserver/api/authors/test-author/entries/1",
            author=self.author,
            content="Public post",
            content_type="text/plain",
            visibility="PUBLIC",
            published=timezone.now(),
        )

        Entry.objects.create(
            url="http://testserver/api/authors/test-author/entries/2",
            author=self.author,
            content="Friends post",
            content_type="text/plain",
            visibility="FRIENDS",
            published=timezone.now(),
        )

    def test_profile_page_shows_author_and_only_public_entries(self):
        resp = self.client.get(reverse("author_profile", args=[self.author.id]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Skar")
        self.assertContains(resp, "Hello! This is my profile.")
        self.assertContains(resp, "Public post")
        self.assertNotContains(resp, "Friends post")



class AuthorEditPageTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            url="http://127.0.0.1:8000/api/authors/test-author",
            host="http://127.0.0.1:8000/api/",
            displayName="Skar",
            github="https://github.com/example",
            description="Hello! This is my profile.",
            profileImage="https://placehold.co/150x150",
            web="http://127.0.0.1:8000/authors/test-author",
        )

    def test_edit_page_post_updates_author_and_redirects(self):
        edit_url = reverse("author_edit", args=[self.author.id])

        resp = self.client.post(edit_url, data={
            "displayName": "Skar Test",
            "github": "https://github.com/skar-test",
            "description": "Updated description",
            "profileImage": "https://placehold.co/200x200",
        })

        # should redirect back to the profile page after save
        self.assertEqual(resp.status_code, 302)

        # confirm the DB actually changed
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, "Skar Test")
        self.assertEqual(self.author.github, "https://github.com/skar-test")
        self.assertEqual(self.author.description, "Updated description")
        self.assertEqual(self.author.profileImage, "https://placehold.co/200x200")