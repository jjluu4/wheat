import uuid
from unittest.mock import patch
from urllib.parse import quote

from django.test import TestCase
from rest_framework.response import Response

from core.tests.assertions import assert_author_shape, assert_collection_shape
from core.tests.factories import make_author, make_local_author, make_remote_node


class AuthorApiTests(TestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="author-owner",
            display_name="Author Owner",
            github="https://github.com/author-owner",
            profile_image="https://placehold.co/64x64.png",
            description="original description",
        )
        self.remote_author = make_author(
            display_name="Remote Cached",
            url="https://partner.example.com/api/authors/cached-remote",
            host="https://partner.example.com/api/",
            web="https://partner.example.com/authors/cached-remote",
            github="https://github.com/cached-remote",
            profile_image="https://partner.example.com/media/avatar.png",
            description="remote cached description",
        )
        self.remote_node = make_remote_node(
            name="Partner Node",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="partner-user",
            password="partner-pass",
        )

    def test_authors_collection_returns_documented_shape(self):
        response = self.client.get("/api/authors/?page=1&size=10")

        self.assertEqual(response.status_code, 200)
        assert_collection_shape(self, response.json(), collection_type="authors", item_key="authors")
        self.assertGreaterEqual(response.json()["count"], 1)
        assert_author_shape(self, response.json()["authors"][0])

    def test_single_author_serial_route_returns_author_shape(self):
        response = self.client.get(f"/api/authors/{self.owner.serial}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        assert_author_shape(self, data)
        self.assertEqual(data["id"], self.owner.url)
        self.assertEqual(data["displayName"], self.owner.displayName)

    def test_single_author_fqid_returns_cached_author_for_authenticated_user(self):
        self.client.force_login(self.owner_user)
        fqid = quote(self.remote_author.url, safe="")

        response = self.client.get(f"/api/authors/{fqid}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        assert_author_shape(self, data)
        self.assertEqual(data["id"], self.remote_author.url)
        self.assertEqual(data["displayName"], self.remote_author.displayName)

    @patch("core.apis.author_api.fetch_remote_resource")
    def test_single_author_fqid_fetches_remote_when_not_cached(self, mock_fetch_remote_resource):
        self.client.force_login(self.owner_user)
        missing_fqid = "https://partner.example.com/api/authors/missing-remote"
        encoded = quote(missing_fqid, safe="")
        mock_fetch_remote_resource.return_value = Response(
            {
                "type": "author",
                "id": missing_fqid,
                "host": "https://partner.example.com/api/",
                "displayName": "Fetched Remote",
                "github": "https://github.com/fetched-remote",
                "profileImage": "https://partner.example.com/media/fetched.png",
                "web": "https://partner.example.com/authors/fetched-remote",
            }
        )

        response = self.client.get(f"/api/authors/{encoded}/")

        self.assertEqual(response.status_code, 200)
        mock_fetch_remote_resource.assert_called_once_with(missing_fqid)

    def test_put_single_author_updates_supported_profile_fields(self):
        self.client.force_login(self.owner_user)

        response = self.client.put(
            f"/api/authors/{self.owner.serial}/",
            data={
                "displayName": "Updated Name",
                "github": "https://github.com/updated-name",
                "profileImage": "https://placehold.co/128x128.png",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.displayName, "Updated Name")
        self.assertEqual(self.owner.github, "https://github.com/updated-name")
        self.assertEqual(self.owner.profileImage, "https://placehold.co/128x128.png")

    def test_put_single_author_does_not_update_description_via_api(self):
        self.client.force_login(self.owner_user)

        response = self.client.put(
            f"/api/authors/{self.owner.serial}/",
            data={
                "displayName": "Name With Description Attempt",
                "description": "new description from API",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.displayName, "Name With Description Attempt")
        self.assertEqual(self.owner.description, "original description")

    def test_single_author_fqid_requires_authenticated_session_or_remote_basic_auth(self):
        fqid = quote(self.remote_author.url, safe="")

        response = self.client.get(f"/api/authors/{fqid}/")

        self.assertEqual(response.status_code, 401)
