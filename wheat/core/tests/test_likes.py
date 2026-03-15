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

    def test_unauthenticated_user_cannot_like_entry(self):
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 401)

    def test_cannot_like_as_different_author(self):
        self.client.force_login(self.friend_user)

        resp = self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_owner_can_like_own_entry(self):
        self.client.force_login(self.owner_user)

        resp = self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.public_entry.url)

    def test_like_entry_with_invalid_object_url_returns_400(self):
        self.client.force_login(self.stranger_user)

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": "garbage"},
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_like_entry_with_missing_object_returns_400(self):
        self.client.force_login(self.stranger_user)

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like"},
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_like_nonexistent_entry_returns_404(self):
        self.client.force_login(self.stranger_user)
        missing_entry_url = f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}/"

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": missing_entry_url},
            format="json",
        )

        self.assertEqual(resp.status_code, 404)

    def test_owner_can_like_own_friends_only_entry(self):
        self.client.force_login(self.owner_user)

        resp = self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)

    def test_admin_with_author_profile_can_like_friends_only_entry(self):
        admin_author = self.make_author(self.admin_user, "Admin")
        self.client.force_login(self.admin_user)

        resp = self.client.post(
            self.like_url(admin_author),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.friends_entry.url)

    def test_unlisted_entry_can_be_liked_by_stranger(self):
        unlisted_entry = self.make_entry(self.owner, "Unlisted entry", visibility="UNLISTED")
        self.client.force_login(self.stranger_user)

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": unlisted_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)

    def test_deleted_entry_cannot_be_liked_by_non_staff(self):
        self.public_entry.visibility = "DELETED"
        self.public_entry.save(update_fields=["visibility"])
        self.client.force_login(self.stranger_user)

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_duplicate_comment_like_is_idempotent(self):
        self.client.force_login(self.stranger_user)

        first = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )
        second = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)

        likes_resp = self.client.get(self.comment_likes_url(self.public_comment))
        self.assertEqual(likes_resp.status_code, 200)
        self.assertEqual(likes_resp.data["count"], 1)

    def test_friend_can_like_comment_on_friends_only_entry(self):
        self.client.force_login(self.friend_user)

        resp = self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.friend_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.friend_comment.url)

    def test_comment_author_can_like_own_hidden_comment(self):
        self.client.force_login(self.former_user)

        resp = self.client.post(
            self.like_url(self.former),
            data={"type": "like", "object": self.former_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.former_comment.url)

    def test_unauthenticated_user_cannot_like_comment(self):
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 401)

    def test_like_nonexistent_comment_returns_404(self):
        self.client.force_login(self.stranger_user)
        missing_comment_url = f"http://testserver/api/authors/{self.friend.serial}/commented/{uuid.uuid4()}/"

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": missing_comment_url},
            format="json",
        )

        self.assertEqual(resp.status_code, 404)

    def test_single_comment_payload_embeds_like_count(self):
        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        resp = self.client.get(f"/api/authors/{self.friend.serial}/commented/{self.public_comment.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("likes", resp.data)
        self.assertEqual(resp.data["likes"]["count"], 1)

    def test_unauthenticated_user_can_see_likes_on_public_entry(self):
        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )
        self.client.logout()

        resp = self.client.get(self.entry_likes_url(self.public_entry))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)

    def test_unauthenticated_user_cannot_see_likes_on_friends_only_entry(self):
        resp = self.client.get(self.entry_likes_url(self.friends_entry))
        self.assertEqual(resp.status_code, 401)

    def test_non_friend_cannot_see_likes_on_friends_only_entry(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.entry_likes_url(self.friends_entry))
        self.assertEqual(resp.status_code, 403)

    def test_friend_can_see_likes_on_friends_only_entry(self):
        self.client.force_login(self.friend_user)
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        resp = self.client.get(self.entry_likes_url(self.friends_entry))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)

    def test_owner_can_see_likes_on_own_friends_only_entry(self):
        self.client.force_login(self.friend_user)
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.client.force_login(self.owner_user)
        resp = self.client.get(self.entry_likes_url(self.friends_entry))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)

    def test_author_liked_filters_hidden_likes_for_viewer(self):
        self.client.force_login(self.friend_user)
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.like_url(self.friend))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["src"][0]["object"], self.public_entry.url)

    def test_non_friend_cannot_see_hidden_comment_likes(self):
        self.client.force_login(self.former_user)
        self.client.post(
            self.like_url(self.former),
            data={"type": "like", "object": self.former_comment.url},
            format="json",
        )

        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.comment_likes_url(self.former_comment))
        self.assertEqual(resp.status_code, 403)

    def test_multiple_users_liking_same_entry_updates_count(self):
        self.client.force_login(self.owner_user)
        self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.client.force_login(self.friend_user)
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        resp = self.client.get(self.entry_likes_url(self.public_entry))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)

    def test_entry_likes_pagination_fields_are_correct(self):
        self.client.force_login(self.owner_user)
        self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.client.force_login(self.friend_user)
        self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        resp = self.client.get(f"{self.entry_likes_url(self.public_entry)}?page=2&size=1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["page_number"], 2)
        self.assertEqual(resp.data["size"], 1)
        self.assertEqual(resp.data["count"], 3)
        self.assertEqual(len(resp.data["src"]), 1)

    def test_owner_sees_all_comments_on_friends_only_entry(self):
        self.client.force_login(self.owner_user)
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")

        self.assertEqual(resp.status_code, 200)
        contents = [comment["content"] for comment in resp.data["src"]]
        self.assertIn("Friends-only comment", contents)
        self.assertIn("Former friend comment", contents)

    def test_unauthenticated_user_cannot_see_comments_on_friends_only_entry(self):
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")
        self.assertEqual(resp.status_code, 403)

    def test_non_friend_cannot_fetch_single_hidden_comment(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.get(f"/api/authors/{self.former.serial}/commented/{self.former_comment.serial}/")
        self.assertEqual(resp.status_code, 403)

    def test_friend_can_fetch_single_comment_on_friends_only_entry(self):
        self.client.force_login(self.friend_user)
        resp = self.client.get(f"/api/authors/{self.friend.serial}/commented/{self.friend_comment.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Friends-only comment")

    def test_non_friend_comment_post_does_not_create_comment(self):
        before = Comment.objects.filter(entry=self.friends_entry, author=self.stranger).count()

        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            f"/api/authors/{self.stranger.serial}/commented/",
            data={
                "type": "comment",
                "entry": self.friends_entry.url,
                "content": "Blocked comment",
            },
            format="json",
        )

        after = Comment.objects.filter(entry=self.friends_entry, author=self.stranger).count()

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(before, 0)
        self.assertEqual(after, 0)
