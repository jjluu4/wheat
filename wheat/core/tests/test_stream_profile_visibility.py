from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Follow
from core.tests.factories import make_author, make_entry, make_local_author, make_user


class StreamAndProfileVisibilityTests(TestCase):
    def setUp(self):
        self.viewer_user, self.viewer = make_local_author(
            username="stream-viewer",
            display_name="Stream Viewer",
        )
        self.followed_user, self.followed = make_local_author(
            username="stream-followed",
            display_name="Followed Author",
        )
        self.friend_user, self.friend = make_local_author(
            username="stream-friend",
            display_name="Friend Author",
        )
        self.stranger_user, self.stranger = make_local_author(
            username="stream-stranger",
            display_name="Stranger Author",
        )
        self.staff_user = make_user(
            username="stream-staff",
            is_staff=True,
            is_superuser=True,
        )
        self.remote_author = make_author(
            display_name="Remote Author",
            host="https://remote.example.com/api/",
            url="https://remote.example.com/api/authors/remote-author",
            web="https://remote.example.com/authors/remote-author/",
        )

        Follow.objects.create(actor=self.viewer, target=self.followed, status="ACCEPTED")
        Follow.objects.create(actor=self.viewer, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.viewer, status="ACCEPTED")

        now = timezone.now()
        self.public_stranger = make_entry(
            author=self.stranger,
            title="Public Stranger",
            content="public-stranger",
            visibility="PUBLIC",
            published=now - timedelta(hours=4),
        )
        self.remote_public = make_entry(
            author=self.remote_author,
            title="Remote Public",
            content="remote-public",
            visibility="PUBLIC",
            url="https://remote.example.com/api/authors/remote-author/entries/remote-public",
            published=now - timedelta(hours=1),
        )
        self.followed_unlisted = make_entry(
            author=self.followed,
            title="Followed Unlisted",
            content="followed-unlisted",
            visibility="UNLISTED",
            published=now - timedelta(hours=3),
        )
        self.friend_public = make_entry(
            author=self.friend,
            title="Friend Public",
            content="friend-public",
            visibility="PUBLIC",
            published=now - timedelta(hours=2),
        )
        self.friend_only = make_entry(
            author=self.friend,
            title="Friend Only",
            content="friend-only",
            visibility="FRIENDS",
            published=now,
        )
        self.friend_deleted = make_entry(
            author=self.friend,
            title="Friend Deleted",
            content="friend-deleted",
            visibility="DELETED",
            published=now + timedelta(minutes=5),
        )

    def test_stream_includes_visible_entries_from_local_and_remote_authors(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse("my_stream"))

        self.assertEqual(response.status_code, 200)
        contents = [entry.content for entry in response.context["entries"]]
        self.assertIn("public-stranger", contents)
        self.assertIn("remote-public", contents)
        self.assertIn("followed-unlisted", contents)
        self.assertIn("friend-only", contents)
        self.assertNotIn("friend-deleted", contents)

    def test_stream_orders_mixed_local_and_remote_entries_newest_first(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse("my_stream"))

        self.assertEqual(response.status_code, 200)
        ordered_contents = [entry.content for entry in response.context["entries"]]
        self.assertEqual(
            ordered_contents[:5],
            [
                "friend-only",
                "remote-public",
                "friend-public",
                "followed-unlisted",
                "public-stranger",
            ],
        )

    def test_stream_stops_showing_friends_entry_after_unfollow_breaks_friendship(self):
        self.client.force_login(self.viewer_user)
        initial = self.client.get(reverse("my_stream"))
        self.assertContains(initial, "friend-only")

        Follow.objects.filter(actor=self.viewer, target=self.friend).delete()

        updated = self.client.get(reverse("my_stream"))

        self.assertEqual(updated.status_code, 200)
        self.assertContains(updated, "friend-public")
        self.assertNotContains(updated, "friend-only")

    def test_profile_page_shows_only_public_entries_to_anonymous_visitors(self):
        response = self.client.get(reverse("author_profile", args=[self.friend.serial]))

        entries = list(response.context["entries"])
        contents = [entry.content for entry in entries]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(contents, ["friend-public"])

    def test_profile_page_shows_unlisted_entries_to_followers(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse("author_profile", args=[self.followed.serial]))

        entries = list(response.context["entries"])
        contents = [entry.content for entry in entries]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(contents, ["followed-unlisted"])

    def test_profile_page_shows_friends_entries_to_mutual_friends(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse("author_profile", args=[self.friend.serial]))

        entries = list(response.context["entries"])
        contents = [entry.content for entry in entries]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(contents, ["friend-only", "friend-public"])

    def test_profile_page_shows_owner_all_non_deleted_entries(self):
        self.client.force_login(self.friend_user)

        response = self.client.get(reverse("author_profile", args=[self.friend.serial]))

        entries = list(response.context["entries"])
        contents = [entry.content for entry in entries]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(contents, ["friend-only", "friend-public"])
        self.assertNotIn("friend-deleted", contents)

    def test_profile_page_shows_deleted_entries_to_staff(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("author_profile", args=[self.friend.serial]))

        entries = list(response.context["entries"])
        contents = [entry.content for entry in entries]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(contents, ["friend-deleted", "friend-only", "friend-public"])
