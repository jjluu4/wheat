from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from unittest.mock import patch
from core.models import Author, Comment, Entry, Follow


class CommentsFQIDAPITests(APITestCase):
    def setUp(self):
        self.owner_user = User.objects.create_user(username="owner", password="pass")
        self.friend_user = User.objects.create_user(username="friend", password="pass")
        self.stranger_user = User.objects.create_user(username="stranger", password="pass")
        self.owner = self.make_author(self.owner_user, "Owner")
        self.friend = self.make_author(self.friend_user, "Friend")
        self.stranger = self.make_author(self.stranger_user, "Stranger")

        Follow.objects.create(actor=self.owner, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.owner, status="ACCEPTED")

        self.public_entry = self.make_entry(self.owner, "Public entry", visibility="PUBLIC")
        self.friends_entry = self.make_entry(self.owner, "Friends entry", visibility="FRIENDS")
        self.unlisted_entry = self.make_entry(self.owner, "Unlisted entry", visibility="UNLISTED")

        self.public_comment = self.make_comment(self.friend, self.public_entry, "Public comment")
        self.friend_comment = self.make_comment(self.friend, self.friends_entry, "Friends only comment")
        self.owner_comment = self.make_comment(self.owner, self.public_entry, "Owner comment")

    def make_author(self, user, display_name):
        serial = uuid.uuid4()
        return Author.objects.create(
            user=user,
            serial=serial,
            url=f"http://testserver/api/authors/{serial}",
            host="http://testserver/api/",
            displayName=display_name,
            github="",
            profileImage="https://example.com/image.png",
            web=f"http://testserver/authors/{serial}/",
        )

    def make_entry(self, author, content, visibility="PUBLIC"):
        serial = uuid.uuid4()
        return Entry.objects.create(
            author=author,
            serial=serial,
            url=f"http://testserver/api/authors/{author.serial}/entries/{serial}/",
            title="Untitled",
            content=content,
            content_type="text/plain",
            visibility=visibility,
            published=timezone.now(),
        )

    def make_comment(self, author, entry, content):
        serial = uuid.uuid4()
        return Comment.objects.create(
            author=author,
            entry=entry,
            serial=serial,
            url=f"http://testserver/api/authors/{author.serial}/commented/{serial}/",
            content_type="text/plain",
            content=content,
            published=timezone.now(),
        )

    def author_commented_fqid_url(self, author):
        from urllib.parse import quote
        return f"/api/authors/{quote(author.url, safe='')}/commented/"

    def comment_fqid_url(self, comment):
        from urllib.parse import quote
        return f"/api/commented/{quote(comment.url, safe='')}/"

    def entry_comments_fqid_url(self, entry):
        from urllib.parse import quote
        return f"/api/entries/{quote(entry.url, safe='')}/comments/"

    # tests for author_commented_fqid

    def test_author_commented_fqid_get_returns_comments(self):
        """GET /api/authors/{author_fqid}/commented/ returns comments for that author."""
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.author_commented_fqid_url(self.owner))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["src"][0]["content"], "Owner comment")

    def test_author_commented_fqid_get_pagination(self):
        """GET respects pagination parameters."""
        for i in range(5):
            self.make_comment(self.friend, self.public_entry, f"Comment {i}")
        self.client.force_login(self.friend_user)
        resp = self.client.get(f"{self.author_commented_fqid_url(self.friend)}?page=1&size=3")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["page_number"], 1)
        self.assertEqual(resp.data["size"], 3)
        self.assertEqual(len(resp.data["src"]), 3)

    def test_author_commented_fqid_get_permission_check(self):
        """GET respects visibility permissions."""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.author_commented_fqid_url(self.owner))
        # stranger should see only public comments from owner
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["src"][0]["content"], "Owner comment")

    def test_author_commented_fqid_get_author_not_found(self):
        """Returns 404 for non-existent author."""
        fake_url = "http://testserver/api/authors/nonexistent"
        from urllib.parse import quote
        resp = self.client.get(f"/api/authors/{quote(fake_url, safe='')}/commented/")
        self.assertEqual(resp.status_code, 404)

    # tests for comment_fqid

    def test_comment_fqid_get_returns_comment(self):
        """GET /api/commented/{comment_fqid}/ returns a single comment."""
        self.client.force_login(self.friend_user)
        resp = self.client.get(self.comment_fqid_url(self.friend_comment))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Friends only comment")

    def test_comment_fqid_get_permission_check(self):
        """GET respects comment visibility permissions."""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.comment_fqid_url(self.friend_comment))
        self.assertEqual(resp.status_code, 403)

    def test_comment_fqid_get_owner_can_view(self):
        """Comment owner can view their own comment."""
        self.client.force_login(self.friend_user)
        resp = self.client.get(self.comment_fqid_url(self.friend_comment))
        self.assertEqual(resp.status_code, 200)

    def test_comment_fqid_get_not_found(self):
        """Returns 404 for non-existent comment."""
        fake_url = "http://testserver/api/authors/owner/commented/fake"
        from urllib.parse import quote
        resp = self.client.get(f"/api/commented/{quote(fake_url, safe='')}/")
        self.assertEqual(resp.status_code, 404)

    # tests for entry_comments_fqid

    def test_entry_comments_fqid_get_returns_comments(self):
        """GET /api/entries/{entry_fqid}/comments/ returns comments for the entry."""
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.entry_comments_fqid_url(self.public_entry))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)

    def test_entry_comments_fqid_get_permission_check(self):
        """GET respects entry visibility."""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.entry_comments_fqid_url(self.friends_entry))
        self.assertEqual(resp.status_code, 403)

    def test_entry_comments_fqid_get_pagination(self):
        """GET respects pagination parameters."""
        for i in range(5):
            self.make_comment(self.friend, self.public_entry, f"Comment {i}")
        self.client.force_login(self.owner_user)
        resp = self.client.get(f"{self.entry_comments_fqid_url(self.public_entry)}?page=1&size=3")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["page_number"], 1)
        self.assertEqual(resp.data["size"], 3)
        self.assertEqual(len(resp.data["src"]), 3)

    def test_entry_comments_fqid_get_entry_not_found(self):
        """Returns 404 for non-existent entry."""
        fake_url = "http://testserver/api/authors/owner/entries/fake"
        from urllib.parse import quote
        resp = self.client.get(f"/api/entries/{quote(fake_url, safe='')}/comments/")
        self.assertEqual(resp.status_code, 404)