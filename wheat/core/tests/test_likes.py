import uuid

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Author, Comment, Entry, Follow


class LikesAndCommentVisibilityTests(APITestCase):
    def setUp(self):
        self.owner_user = User.objects.create_user(username="owner", password="pass12345")
        self.friend_user = User.objects.create_user(username="friend", password="pass12345")
        self.stranger_user = User.objects.create_user(username="stranger", password="pass12345")
        self.former_user = User.objects.create_user(username="former", password="pass12345")
        self.admin_user = User.objects.create_superuser(username="admin", password="pass12345", email="admin@example.com")

        self.owner = self.make_author(self.owner_user, "Owner")
        self.friend = self.make_author(self.friend_user, "Friend")
        self.stranger = self.make_author(self.stranger_user, "Stranger")
        self.former = self.make_author(self.former_user, "Former")

        Follow.objects.create(actor=self.owner, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.owner, status="ACCEPTED")

        self.public_entry = self.make_entry(self.owner, "Public entry", visibility="PUBLIC")
        self.friends_entry = self.make_entry(self.owner, "Friends entry", visibility="FRIENDS")

        self.public_comment = self.make_comment(self.friend, self.public_entry, "Public comment")
        self.friend_comment = self.make_comment(self.friend, self.friends_entry, "Friends-only comment")
        self.former_comment = self.make_comment(self.former, self.friends_entry, "Former friend comment")

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

    def like_url(self, author):
        return f"/api/authors/{author.serial}/liked/"

    def entry_likes_url(self, entry):
        return f"/api/authors/{entry.author.serial}/entries/{entry.serial}/likes/"

    def comment_likes_url(self, comment):
        return f"/api/authors/{comment.entry.author.serial}/entries/{comment.entry.serial}/comments/{comment.serial}/likes/"

    def test_like_public_entry(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["type"], "like")
        self.assertEqual(resp.data["object"], self.public_entry.url)

        likes_resp = self.client.get(self.entry_likes_url(self.public_entry))
        self.assertEqual(likes_resp.status_code, 200)
        self.assertEqual(likes_resp.data["count"], 1)
        self.assertEqual(likes_resp.data["src"][0]["author"]["displayName"], "Stranger")

    def test_like_friends_entry_as_friend(self):
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.friends_entry.url)

    def test_like_friends_entry_as_non_friend_is_blocked(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_duplicate_entry_like_is_idempotent(self):
        self.client.force_login(self.stranger_user)

        first = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )
        second = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)

        likes_resp = self.client.get(self.entry_likes_url(self.public_entry))
        self.assertEqual(likes_resp.data["count"], 1)

    def test_like_public_comment(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.public_comment.url)

        likes_resp = self.client.get(self.comment_likes_url(self.public_comment))
        self.assertEqual(likes_resp.status_code, 200)
        self.assertEqual(likes_resp.data["count"], 1)
        self.assertIn("id", likes_resp.data["src"][0])

    def test_like_hidden_comment_is_blocked(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.friend_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_author_liked_returns_entry_and_comment_likes(self):
        self.client.force_login(self.friend_user)
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        resp = self.client.get(self.like_url(self.friend))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)
        objects = [item["object"] for item in resp.data["src"]]
        self.assertIn(self.public_entry.url, objects)
        self.assertIn(self.public_comment.url, objects)

    def test_single_entry_embeds_likes_collection(self):
        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )
        self.client.logout()

        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("likes", resp.data)
        self.assertEqual(resp.data["likes"]["count"], 1)

    def test_author_entries_embed_likes_collection(self):
        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )
        self.client.logout()

        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["src"][0]["likes"]["count"], 1)

    def test_friends_entry_comments_friend_sees_all(self):
        self.client.force_login(self.friend_user)
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")

        self.assertEqual(resp.status_code, 200)
        contents = [comment["content"] for comment in resp.data["src"]]
        self.assertIn("Friends-only comment", contents)
        self.assertIn("Former friend comment", contents)

    def test_friends_entry_comments_non_friend_blocked(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")
        self.assertEqual(resp.status_code, 403)

    def test_friends_entry_comment_author_sees_only_own_comment(self):
        self.client.force_login(self.former_user)
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")

        self.assertEqual(resp.status_code, 200)
        contents = [comment["content"] for comment in resp.data["src"]]
        self.assertEqual(contents, ["Former friend comment"])

    def test_author_commented_get_filters_hidden_comments(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.get(f"/api/authors/{self.former.serial}/commented/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 0)

    def test_author_commented_post_blocks_inaccessible_entry(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            f"/api/authors/{self.stranger.serial}/commented/",
            data={
                "type": "comment",
                "entry": self.friends_entry.url,
                "content": "I should not be able to post this",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_comment_author_can_fetch_single_hidden_comment(self):
        self.client.force_login(self.former_user)
        resp = self.client.get(f"/api/authors/{self.former.serial}/commented/{self.former_comment.serial}/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Former friend comment")
