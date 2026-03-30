import urllib.parse

from rest_framework.test import APITestCase

from core.tests.assertions import assert_entry_shape
from core.tests.factories import make_entry, make_follow, make_local_author, make_user


class EntryVisibilityApiTests(APITestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="visibility-owner",
            display_name="Visibility Owner",
        )
        self.friend_user, self.friend = make_local_author(
            username="visibility-friend",
            display_name="Visibility Friend",
        )
        self.follower_user, self.follower = make_local_author(
            username="visibility-follower",
            display_name="Visibility Follower",
        )
        self.stranger_user, self.stranger = make_local_author(
            username="visibility-stranger",
            display_name="Visibility Stranger",
        )
        self.staff_user = make_user(
            username="visibility-staff",
            is_staff=True,
            is_superuser=True,
        )

        make_follow(actor=self.owner, target=self.friend, status="ACCEPTED")
        make_follow(actor=self.friend, target=self.owner, status="ACCEPTED")
        make_follow(actor=self.follower, target=self.owner, status="ACCEPTED")

        self.public_entry = make_entry(
            author=self.owner,
            title="Public Entry",
            content="Public body",
            visibility="PUBLIC",
        )
        self.unlisted_entry = make_entry(
            author=self.owner,
            title="Unlisted Entry",
            content="Unlisted body",
            visibility="UNLISTED",
        )
        self.friends_entry = make_entry(
            author=self.owner,
            title="Friends Entry",
            content="Friends body",
            visibility="FRIENDS",
        )
        self.deleted_entry = make_entry(
            author=self.owner,
            title="Deleted Entry",
            content="Deleted body",
            visibility="DELETED",
        )

    def test_single_entry_direct_link_allows_unlisted_for_anonymous_viewer(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.unlisted_entry.serial}/"
        )

        self.assertEqual(response.status_code, 200)
        assert_entry_shape(self, response.json())
        self.assertEqual(response.json()["visibility"], "UNLISTED")

    def test_single_entry_direct_link_requires_authentication_for_friends_entry(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/"
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "Authentication required")

    def test_single_entry_direct_link_forbids_logged_in_non_friend_for_friends_entry(self):
        self.client.force_login(self.stranger_user)

        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"],
            "You don't have permission to view this entry",
        )

    def test_single_entry_visibility_transition_public_to_friends_takes_effect_immediately(self):
        self.client.force_login(self.owner_user)
        update = self.client.put(
            f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/",
            data={"visibility": "FRIENDS"},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.public_entry.refresh_from_db()
        self.assertEqual(self.public_entry.visibility, "FRIENDS")

        self.client.logout()
        anonymous = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/"
        )
        self.assertEqual(anonymous.status_code, 401)

        self.client.force_login(self.friend_user)
        friend_response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/"
        )
        self.assertEqual(friend_response.status_code, 200)
        self.assertEqual(friend_response.json()["visibility"], "FRIENDS")

    def test_single_entry_visibility_transition_friends_to_public_takes_effect_immediately(self):
        self.client.force_login(self.stranger_user)
        blocked = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/"
        )
        self.assertEqual(blocked.status_code, 403)

        self.client.force_login(self.owner_user)
        update = self.client.put(
            f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/",
            data={"visibility": "PUBLIC"},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.friends_entry.refresh_from_db()
        self.assertEqual(self.friends_entry.visibility, "PUBLIC")

        self.client.force_login(self.stranger_user)
        allowed = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/"
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["visibility"], "PUBLIC")

    def test_single_entry_deleted_entry_returns_not_found_for_non_admin(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.deleted_entry.serial}/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Entry not found")

    def test_single_entry_deleted_entry_remains_visible_to_staff(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.deleted_entry.serial}/"
        )

        self.assertEqual(response.status_code, 200)
        assert_entry_shape(self, response.json())
        self.assertEqual(response.json()["visibility"], "DELETED")

    def test_entry_fqid_direct_link_allows_unlisted_for_anonymous_viewer(self):
        encoded = urllib.parse.quote(self.unlisted_entry.url, safe="")

        response = self.client.get(f"/api/entries/{encoded}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.unlisted_entry.url)
        self.assertEqual(response.json()["visibility"], "UNLISTED")

    def test_entry_fqid_deleted_entry_returns_forbidden_for_non_admin_current_behavior(self):
        encoded = urllib.parse.quote(self.deleted_entry.url, safe="")

        response = self.client.get(f"/api/entries/{encoded}/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"],
            "You do not have permission to view this entry.",
        )

    def test_entry_fqid_deleted_entry_remains_visible_to_staff(self):
        encoded = urllib.parse.quote(self.deleted_entry.url, safe="")
        self.client.force_login(self.staff_user)

        response = self.client.get(f"/api/entries/{encoded}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.deleted_entry.url)
        self.assertEqual(response.json()["visibility"], "DELETED")
