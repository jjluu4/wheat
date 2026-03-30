import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Author, Comment, CommentLike, Entry, EntryLike, Follow


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
        """Stranger can like a public entry and likes collection reflects it."""
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
        """Friend can like a friends-only entry."""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.like_url(self.friend),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.friends_entry.url)

    def test_like_friends_entry_as_non_friend_is_blocked(self):
        """Non-friend cannot like a friends-only entry."""
        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_duplicate_entry_like_is_idempotent(self):
        """Liking the same entry twice returns existing like and keeps count at one."""
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

    @patch("core.apis.like_api.EntryLike.objects.create")
    def test_entry_like_recovers_from_uniqueness_race(self, mock_create):
        self.client.force_login(self.stranger_user)

        def create_then_raise(*args, **kwargs):
            like = EntryLike(**kwargs)
            like.save(force_insert=True)
            raise IntegrityError("duplicate key value violates unique constraint")

        mock_create.side_effect = create_then_raise
        response = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        likes_resp = self.client.get(self.entry_likes_url(self.public_entry))
        self.assertEqual(likes_resp.data["count"], 1)

    def test_like_public_comment(self):
        """Stranger can like a public comment and comment likes collection reflects it."""
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

    @patch("core.apis.like_api.send_json_to_remote_author_inbox")
    def test_like_public_remote_entry_uses_shared_inbox_helper(self, mock_send):
        remote_owner = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-entry-owner",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Entry Owner",
            github="",
            profileImage="https://example.com/image.png",
            web="http://remote-node-a.example.com/authors/remote-entry-owner/",
        )
        remote_entry = Entry.objects.create(
            author=remote_owner,
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-entry-owner/entries/remote-entry/",
            title="Remote public entry",
            content="hello",
            content_type="text/plain",
            visibility="PUBLIC",
            published=timezone.now(),
        )

        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": remote_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], remote_owner.url)
        self.assertEqual(mock_send.call_args.kwargs["timeout"], 5)
        self.assertEqual(mock_send.call_args.args[1]["type"], "like")
        self.assertEqual(mock_send.call_args.args[1]["object"], remote_entry.url)

    def test_like_hidden_comment_is_blocked(self):
        """Non-author, non-friend cannot like a hidden friends-only comment."""
        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.friend_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_author_liked_returns_entry_and_comment_likes(self):
        """GET /liked/ for an author returns both entry and comment likes."""
        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        resp = self.client.get(self.like_url(self.stranger))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)
        objects = [item["object"] for item in resp.data["src"]]
        self.assertIn(self.public_entry.url, objects)
        self.assertIn(self.public_comment.url, objects)

    def test_single_entry_embeds_likes_collection(self):
        """Single entry API payload embeds a likes collection with correct count."""
        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("likes", resp.data)
        self.assertEqual(resp.data["likes"]["count"], 1)
        self.assertTrue(resp.data["likes"]["viewer_has_liked"])

    def test_author_profile_renders_liked_entry_button_state(self):
        """Author profile renders the entry like button with the viewer's current like state."""
        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        resp = self.client.get(f"/authors/{self.owner.serial}/")

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'class="entry-like-button"')
        self.assertContains(resp, 'data-liked="1"')
        self.assertContains(resp, ">Liked</button>", html=False)

    def test_author_entries_embed_likes_collection(self):
        """Author entries API embeds likes collection for each entry."""
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
        """Friend sees all comments on a friends-only entry."""
        self.client.force_login(self.friend_user)
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")

        self.assertEqual(resp.status_code, 200)
        contents = [comment["content"] for comment in resp.data["src"]]
        self.assertIn("Friends-only comment", contents)
        self.assertIn("Former friend comment", contents)

    def test_friends_entry_comments_non_friend_blocked(self):
        """Non-friend is blocked from seeing comments on a friends-only entry."""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")
        self.assertEqual(resp.status_code, 403)

    def test_friends_entry_comment_author_sees_only_own_comment(self):
        """Former friend can see only their own comment on a friends-only entry."""
        self.client.force_login(self.former_user)
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")

        self.assertEqual(resp.status_code, 200)
        contents = [comment["content"] for comment in resp.data["src"]]
        self.assertEqual(contents, ["Former friend comment"])

    def test_author_commented_get_filters_hidden_comments(self):
        """Author commented API hides comments the viewer should not see."""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(f"/api/authors/{self.former.serial}/commented/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 0)

    def test_author_commented_post_blocks_inaccessible_entry(self):
        """Comment POST is rejected when viewer cannot see the target entry."""
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
        """Comment author can fetch their own hidden comment."""
        self.client.force_login(self.former_user)
        resp = self.client.get(f"/api/authors/{self.former.serial}/commented/{self.former_comment.serial}/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Former friend comment")

    def test_unauthenticated_user_cannot_like_entry(self):
        """Unauthenticated user cannot like any entry."""
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 401)

    def test_cannot_like_as_different_author(self):
        """User cannot send likes as another author."""
        self.client.force_login(self.friend_user)

        resp = self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_owner_can_like_own_entry(self):
        """Entry owner can like their own entry."""
        self.client.force_login(self.owner_user)

        resp = self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.public_entry.url)

    def test_like_entry_with_invalid_object_url_returns_400(self):
        """Liking with an invalid object URL returns a 400 error."""
        self.client.force_login(self.stranger_user)

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": "garbage"},
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_like_entry_with_missing_object_returns_400(self):
        """Liking without an object field returns a 400 error."""
        self.client.force_login(self.stranger_user)

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like"},
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_like_nonexistent_entry_returns_404(self):
        """Liking a non-existent entry returns a 404 error."""
        self.client.force_login(self.stranger_user)
        missing_entry_url = f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}/"

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": missing_entry_url},
            format="json",
        )

        self.assertEqual(resp.status_code, 404)

    def test_owner_can_like_own_friends_only_entry(self):
        """Owner can like their own friends-only entry."""
        self.client.force_login(self.owner_user)

        resp = self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.friends_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)

    def test_admin_with_author_profile_can_like_friends_only_entry(self):
        """Admin with an author profile can like a friends-only entry."""
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
        """Unlisted entry can be liked by a stranger."""
        unlisted_entry = self.make_entry(self.owner, "Unlisted entry", visibility="UNLISTED")
        self.client.force_login(self.stranger_user)

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": unlisted_entry.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)

    def test_deleted_entry_cannot_be_liked_by_non_staff(self):
        """Non-staff user cannot like a deleted entry."""
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
        """Comment likes are idempotent and only one like is stored per author."""
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

    @patch("core.apis.like_api.CommentLike.objects.create")
    def test_comment_like_recovers_from_uniqueness_race(self, mock_create):
        self.client.force_login(self.stranger_user)

        def create_then_raise(*args, **kwargs):
            like = CommentLike(**kwargs)
            like.save(force_insert=True)
            raise IntegrityError("duplicate key value violates unique constraint")

        mock_create.side_effect = create_then_raise
        response = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        likes_resp = self.client.get(self.comment_likes_url(self.public_comment))
        self.assertEqual(likes_resp.status_code, 200)
        self.assertEqual(likes_resp.data["count"], 1)

    def test_friend_can_like_comment_on_friends_only_entry(self):
        """Friend can like a comment on a friends-only entry."""
        self.client.force_login(self.owner_user)

        resp = self.client.post(
            self.like_url(self.owner),
            data={"type": "like", "object": self.friend_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["object"], self.friend_comment.url)

    def test_comment_author_cannot_like_own_hidden_comment(self):
        """Comment author cannot like their own hidden comment."""
        self.client.force_login(self.former_user)

        resp = self.client.post(
            self.like_url(self.former),
            data={"type": "like", "object": self.former_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.data["error"], "You cannot like your own comment")

        likes_resp = self.client.get(self.comment_likes_url(self.former_comment))
        self.assertEqual(likes_resp.status_code, 200)
        self.assertEqual(likes_resp.data["count"], 0)

    def test_unauthenticated_user_cannot_like_comment(self):
        """Unauthenticated user cannot like a comment."""
        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        self.assertEqual(resp.status_code, 401)

    def test_like_nonexistent_comment_returns_404(self):
        """Liking a non-existent comment returns a 404 error."""
        self.client.force_login(self.stranger_user)
        missing_comment_url = f"http://testserver/api/authors/{self.friend.serial}/commented/{uuid.uuid4()}/"

        resp = self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": missing_comment_url},
            format="json",
        )

        self.assertEqual(resp.status_code, 404)

    def test_single_comment_payload_embeds_like_count_and_viewer_state(self):
        """Single comment API payload embeds like count and viewer liked state."""
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
        self.assertTrue(resp.data["likes"]["viewer_has_liked"])

    def test_comments_collection_marks_other_viewer_like_state_false(self):
        """Comments collection reports viewer_has_liked=false for a different viewer."""
        self.client.force_login(self.stranger_user)
        self.client.post(
            self.like_url(self.stranger),
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        self.client.force_login(self.owner_user)
        resp = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/comments/"
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["src"][0]["likes"]["count"], 1)
        self.assertFalse(resp.data["src"][0]["likes"]["viewer_has_liked"])

    def test_unauthenticated_user_can_see_likes_on_public_entry(self):
        """Unauthenticated user can view likes on a public entry."""
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
        """Unauthenticated user cannot see likes on a friends-only entry."""
        resp = self.client.get(self.entry_likes_url(self.friends_entry))
        self.assertEqual(resp.status_code, 401)

    def test_non_friend_cannot_see_likes_on_friends_only_entry(self):
        """Non-friend cannot see likes on a friends-only entry."""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.entry_likes_url(self.friends_entry))
        self.assertEqual(resp.status_code, 403)

    def test_friend_can_see_likes_on_friends_only_entry(self):
        """Friend can see likes on a friends-only entry."""
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
        """Owner can see likes on their own friends-only entry."""
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
        """Author liked collection filters out likes the viewer cannot see."""
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
        """Non-friend cannot see likes on a hidden comment."""
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
        """Multiple users liking the same entry increments the like count."""
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
        """Entry likes endpoint exposes correct pagination metadata."""
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
        """Owner sees all comments on their friends-only entry."""
        self.client.force_login(self.owner_user)
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")

        self.assertEqual(resp.status_code, 200)
        contents = [comment["content"] for comment in resp.data["src"]]
        self.assertIn("Friends-only comment", contents)
        self.assertIn("Former friend comment", contents)

    def test_unauthenticated_user_cannot_see_comments_on_friends_only_entry(self):
        """Unauthenticated user cannot see comments on a friends-only entry."""
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/comments/")
        self.assertEqual(resp.status_code, 403)

    def test_non_friend_cannot_fetch_single_hidden_comment(self):
        """Non-friend cannot fetch a single hidden comment."""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(f"/api/authors/{self.former.serial}/commented/{self.former_comment.serial}/")
        self.assertEqual(resp.status_code, 403)

    def test_friend_can_fetch_single_comment_on_friends_only_entry(self):
        """Friend can fetch a single comment on a friends-only entry."""
        self.client.force_login(self.friend_user)
        resp = self.client.get(f"/api/authors/{self.friend.serial}/commented/{self.friend_comment.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Friends-only comment")

    def test_non_friend_comment_post_does_not_create_comment(self):
        """Non-friend POSTing a comment to a friends-only entry does not create it."""
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
