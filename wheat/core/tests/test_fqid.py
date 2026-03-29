import uuid

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from urllib.parse import quote

from core.models import Author, Comment, Entry, Follow


class FQIDApiTests(APITestCase):
    def setUp(self):
        self.owner_user = User.objects.create_user(username="owner-fqid", password="pass12345")
        self.friend_user = User.objects.create_user(username="friend-fqid", password="pass12345")

        self.owner = self.make_author(self.owner_user, "Owner FQID")
        self.friend = self.make_author(self.friend_user, "Friend FQID")

        Follow.objects.create(actor=self.owner, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.owner, status="ACCEPTED")

        self.entry = self.make_entry(self.owner, "FQID entry")
        self.comment = self.make_comment(self.friend, self.entry, "FQID comment")

    def make_author(self, user, display_name):
        serial = uuid.uuid4()
        return Author.objects.create(
            user=user,
            serial=serial,
            url=f"http://testserver/api/authors/{serial}",
            host="http://testserver/api/",
            displayName=display_name,
            github="https://github.com/example",
            profileImage="https://example.com/image.png",
            web=f"http://testserver/authors/{serial}/",
        )

    def make_entry(self, author, content):
        serial = uuid.uuid4()
        return Entry.objects.create(
            author=author,
            serial=serial,
            url=f"http://testserver/api/authors/{author.serial}/entries/{serial}/",
            title="FQID Entry",
            content=content,
            content_type="text/plain",
            visibility="PUBLIC",
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

    def like_url(self, author):
        return f"/api/authors/{author.serial}/liked/"

    def fqid_segment(self, url):
        return quote(url, safe="")

    def test_author_id_is_full_url(self):
        resp = self.client.get(f"/api/authors/{self.owner.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], self.owner.url)
        self.assertTrue(resp.data["id"].startswith("http://"))

    def test_entry_payload_uses_full_urls(self):
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], self.entry.url)
        self.assertEqual(resp.data["author"]["id"], self.owner.url)
        self.assertEqual(resp.data["comments"]["id"], f"{self.entry.url.rstrip('/')}/comments/")
        self.assertEqual(resp.data["likes"]["id"], f"{self.entry.url.rstrip('/')}/likes/")

    def test_comment_payload_uses_full_urls(self):
        self.client.force_login(self.friend_user)
        resp = self.client.get(f"/api/authors/{self.friend.serial}/commented/{self.comment.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], self.comment.url)
        self.assertEqual(resp.data["entry"], self.entry.url)
        self.assertEqual(resp.data["author"]["id"], self.friend.url)
        self.assertEqual(
            resp.data["likes"]["id"],
            f"{self.entry.url.rstrip('/')}/comments/{self.comment.serial}/likes/",
        )

    def test_comment_collection_has_full_url_id(self):
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/comments/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], f"{self.entry.url.rstrip('/')}/comments/")
        self.assertEqual(resp.data["web"], f"http://testserver/authors/{self.owner.serial}/entries/{self.entry.serial}/")

    def test_like_creation_accepts_trailing_slash_variant_for_entry_url(self):
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.entry.url.rstrip("/")},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.entry.url)
        self.assertTrue(resp.data["id"].startswith("http://"))

    def test_comment_creation_accepts_trailing_slash_variant_for_entry_url(self):
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            f"/api/authors/{self.friend.serial}/commented/",
            data={
                "type": "comment",
                "entry": self.entry.url.rstrip("/"),
                "content": "Slash-normalized comment",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["entry"], self.entry.url)
        self.assertTrue(resp.data["id"].startswith("http://"))

    def test_entry_likes_fqid_matches_serial_route(self):
        self.client.force_login(self.friend_user)
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.entry.url},
            format="json",
        )
        fqid_path = self.fqid_segment(self.entry.url)
        resp = self.client.get(f"/api/entries/{fqid_path}/likes/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["id"], f"{self.entry.url.rstrip('/')}/likes/")

    def test_author_liked_fqid_get_and_post(self):
        self.client.force_login(self.friend_user)
        fqid_path = self.fqid_segment(self.friend.url)
        post_resp = self.client.post(
            f"/api/authors/{fqid_path}/liked/",
            data={"type": "like", "object": self.entry.url},
            format="json",
        )
        self.assertEqual(post_resp.status_code, 201)
        get_resp = self.client.get(f"/api/authors/{fqid_path}/liked/")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.data["count"], 1)

    def test_like_fqid_returns_entry_like(self):
        self.client.force_login(self.friend_user)
        post_resp = self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.entry.url},
            format="json",
        )
        self.assertEqual(post_resp.status_code, 201)
        like_url = post_resp.data["id"]
        fqid_path = self.fqid_segment(like_url)
        resp = self.client.get(f"/api/liked/{fqid_path}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["object"], self.entry.url)

    def test_like_fqid_unknown_returns_404(self):
        fake = quote("http://testserver/api/authors/00000000-0000-0000-0000-000000000001/liked/00000000-0000-0000-0000-000000000099/", safe="")
        resp = self.client.get(f"/api/liked/{fake}/")
        self.assertEqual(resp.status_code, 404)
