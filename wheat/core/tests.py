from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
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
            url="http://testserver/api/authors/test-author",
            host="http://testserver/api/",
            displayName="Skar",
            github="https://github.com/example",
            description="Hello! This is my profile.",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/test-author",
        )

    def test_edit_page_post_updates_author_and_redirects(self):
        edit_url = reverse("author_edit", args=[self.author.id])

        resp = self.client.post(
            edit_url,
            data={
                "displayName": "Skar Test",
                "github": "https://github.com/skar-test",
                "description": "Updated description",
                "profileImage": "https://placehold.co/200x200.png",
            },
        )

        # should redirect back to the profile page after save
        self.assertEqual(resp.status_code, 302)

        # confirm the DB actually changed
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, "Skar Test")
        self.assertEqual(self.author.github, "https://github.com/skar-test")
        self.assertEqual(self.author.description, "Updated description")
        self.assertEqual(self.author.profileImage, "https://placehold.co/200x200.png")


class GitHubAutoImportTests(TestCase):
    @patch("core.views.fetch_public_events")
    def test_profile_page_auto_imports_github_events_without_duplicates(self, mock_fetch):
        # Fake GitHub events (no network)
        mock_fetch.return_value = [
            {
                "id": "111",
                "type": "PushEvent",
                "actor": {"login": "torvalds"},
                "repo": {"name": "torvalds/linux"},
                "payload": {"commits": []},
                "created_at": "2026-03-01T00:00:00Z",
            },
            {
                "id": "222",
                "type": "PushEvent",
                "actor": {"login": "torvalds"},
                "repo": {"name": "torvalds/linux"},
                "payload": {"commits": []},
                "created_at": "2026-03-01T00:05:00Z",
            },
        ]

        author = Author.objects.create(
            url="http://testserver/api/authors/1",
            host="http://testserver/api/",
            displayName="Skar",
            github="https://github.com/torvalds",
            description="",
            profileImage="https://example.com/p.png",
            web="http://testserver/authors/1",
        )

        url = reverse("author_profile", args=[author.id])

        before = Entry.objects.filter(author=author).count()

        self.client.get(url)
        mock_fetch.assert_called()  # ensure view called GitHub fetch
        after_first = Entry.objects.filter(author=author).count()

        # should import 2 entries
        self.assertEqual(after_first, before + 2)

        # visiting again should not duplicate (same github ids)
        self.client.get(url)
        after_second = Entry.objects.filter(author=author).count()
        self.assertEqual(after_second, after_first)


class AuthorListPageTests(TestCase):
    def test_author_list_page(self):
        a = Author.objects.create(
            url="http://testserver/api/authors/test-author",
            host="http://testserver/api/",
            displayName="Skar",
            github="https://github.com/example",
            description="Hi",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/1",
        )
        resp = self.client.get(reverse("author_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Skar")