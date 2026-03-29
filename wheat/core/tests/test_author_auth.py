from urllib.parse import quote

from django.contrib.auth.models import User
from django.test import TestCase

from core.tests.factories import make_author, make_local_author, make_remote_node


class AuthorAuthAndRecoveryTests(TestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="profile-owner",
            display_name="Profile Owner",
        )
        self.other_user, self.other_author = make_local_author(
            username="other-author",
            display_name="Other Author",
        )
        self.remote_author = make_author(
            display_name="Remote Basic",
            url="https://partner.example.com/api/authors/remote-basic",
            host="https://partner.example.com/api/",
            web="https://partner.example.com/authors/remote-basic",
        )
        self.remote_node = make_remote_node(
            name="Partner Node",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="partner-user",
            password="partner-pass",
        )

    def test_signup_creates_inactive_user_without_author_profile(self):
        response = self.client.post(
            "/accounts/signup/",
            data={
                "username": "pending-signup",
                "password1": "complicated-pass-123",
                "password2": "complicated-pass-123",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="pending-signup")
        self.assertFalse(user.is_active)
        self.assertFalse(hasattr(user, "author_profile"))

    def test_put_single_author_requires_authentication(self):
        response = self.client.put(
            f"/api/authors/{self.owner.serial}/",
            data={"displayName": "Should Fail"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_put_single_author_forbids_non_owner(self):
        self.client.force_login(self.other_user)

        response = self.client.put(
            f"/api/authors/{self.owner.serial}/",
            data={"displayName": "Should Also Fail"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_single_author_fqid_allows_remote_basic_auth_for_cached_author(self):
        encoded = quote(self.remote_author.url, safe="")

        response = self.client.get(
            f"/api/authors/{encoded}/",
            HTTP_AUTHORIZATION="Basic cGFydG5lci11c2VyOnBhcnRuZXItcGFzcw==",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.remote_author.url)

    def test_my_stream_creates_missing_author_profile_for_logged_in_user(self):
        user = User.objects.create_user(
            username="stream-recovery",
            password="pass12345",
            is_active=True,
        )
        self.assertFalse(hasattr(user, "author_profile"))
        self.client.force_login(user)

        response = self.client.get("/stream/")

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(hasattr(user, "author_profile"))
        self.assertEqual(user.author_profile.displayName, "stream-recovery")

    def test_my_profile_creates_missing_author_profile_for_logged_in_user(self):
        user = User.objects.create_user(
            username="profile-recovery",
            password="pass12345",
            is_active=True,
        )
        self.assertFalse(hasattr(user, "author_profile"))
        self.client.force_login(user)

        response = self.client.get("/authors/me/")

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(hasattr(user, "author_profile"))
        self.assertIn(str(user.author_profile.serial), response["Location"])
