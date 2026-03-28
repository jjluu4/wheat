import uuid
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase

from core.helpers import (
    build_author_profile_image_url,
    build_browser_entry_image_url,
    build_media_proxy_url,
    get_allowlisted_remote_node_for_media_url,
    is_allowlisted_media_url,
    is_same_node_media_url,
)
from core.models import Author, Entry, RemoteNode


class MediaHelperTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.author = Author.objects.create(
            displayName="Media Owner",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
            host="http://testserver/api/",
            web=f"http://testserver/authors/{uuid.uuid4()}",
        )
        self.entry = Entry.objects.create(
            author=self.author,
            url=f"http://testserver/api/authors/{self.author.serial}/entries/{uuid.uuid4()}",
            content="image entry",
            content_type="image",
            visibility="PUBLIC",
        )
        self.remote_node = RemoteNode.objects.create(
            name="Partner Node",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="partner-user",
            password="partner-pass",
            is_active=True,
        )

    def test_build_author_profile_image_url_returns_same_node_path(self):
        self.assertEqual(
            build_author_profile_image_url(self.author),
            f"/api/authors/{self.author.serial}/profile-image/",
        )
        self.assertEqual(
            build_author_profile_image_url(self.author, self.request),
            f"http://testserver/api/authors/{self.author.serial}/profile-image/",
        )

    def test_build_browser_entry_image_url_returns_same_node_path(self):
        self.assertEqual(
            build_browser_entry_image_url(self.entry),
            f"/api/authors/{self.author.serial}/entries/{self.entry.serial}/image/",
        )
        self.assertEqual(
            build_browser_entry_image_url(self.entry, self.request),
            f"http://testserver/api/authors/{self.author.serial}/entries/{self.entry.serial}/image/",
        )

    def test_build_media_proxy_url_encodes_query_param(self):
        proxied = build_media_proxy_url("https://partner.example.com/media/avatar.png")
        self.assertEqual(
            proxied,
            "/api/media/image-proxy/?url=https%3A%2F%2Fpartner.example.com%2Fmedia%2Favatar.png",
        )

    def test_same_node_media_url_accepts_relative_and_same_origin_urls(self):
        self.assertTrue(is_same_node_media_url("/media/avatar.png", self.request))
        self.assertTrue(is_same_node_media_url("http://testserver/media/avatar.png", self.request))
        self.assertFalse(is_same_node_media_url("https://partner.example.com/media/avatar.png", self.request))

    def test_allowlisted_media_url_accepts_active_remote_node(self):
        url = "https://partner.example.com/media/avatar.png"
        self.assertTrue(is_allowlisted_media_url(url, self.request))
        self.assertEqual(
            get_allowlisted_remote_node_for_media_url(url, self.request),
            self.remote_node,
        )

    def test_allowlisted_media_url_rejects_unconfigured_external_host(self):
        url = "https://evil.example.com/media/avatar.png"
        self.assertFalse(is_allowlisted_media_url(url, self.request))
        self.assertIsNone(get_allowlisted_remote_node_for_media_url(url, self.request))


class MediaProxyApiTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            displayName="Proxy Author",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
            host="http://testserver/api/",
            web=f"http://testserver/authors/{uuid.uuid4()}",
            profileImage="https://partner.example.com/media/avatar.png",
        )
        self.remote_node = RemoteNode.objects.create(
            name="Partner Node",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="partner-user",
            password="partner-pass",
            is_active=True,
        )

    def test_image_proxy_redirects_same_node_url(self):
        resp = self.client.get("/api/media/image-proxy/", {"url": "http://testserver/media/avatar.png"})

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/media/avatar.png")

    @patch("core.helpers.requests.get")
    def test_image_proxy_fetches_allowlisted_remote_image_with_auth(self, mock_get):
        mock_response = Mock(status_code=200, content=b"PNGDATA")
        mock_response.headers = {"Content-Type": "image/png"}
        mock_get.return_value = mock_response

        resp = self.client.get("/api/media/image-proxy/", {"url": "https://partner.example.com/media/avatar.png"})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"PNGDATA")
        self.assertEqual(resp["Content-Type"], "image/png")
        mock_get.assert_called_once()
        self.assertEqual(
            mock_get.call_args.kwargs["headers"]["Authorization"],
            "Basic cGFydG5lci11c2VyOnBhcnRuZXItcGFzcw==",
        )

    def test_image_proxy_rejects_unallowlisted_host(self):
        resp = self.client.get("/api/media/image-proxy/", {"url": "https://evil.example.com/media/avatar.png"})

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"], "Image URL is not allowlisted.")

    @patch("core.helpers.requests.get")
    def test_image_proxy_returns_not_found_for_missing_remote_image(self, mock_get):
        mock_response = Mock(status_code=404)
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_get.return_value = mock_response

        resp = self.client.get("/api/media/image-proxy/", {"url": "https://partner.example.com/media/missing.png"})

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"], "Image not found on remote node.")

    @patch("core.helpers.requests.get")
    def test_author_profile_image_proxies_remote_avatar(self, mock_get):
        mock_response = Mock(status_code=200, content=b"AVATAR")
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_get.return_value = mock_response

        resp = self.client.get(f"/api/authors/{self.author.serial}/profile-image/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"AVATAR")
        self.assertEqual(resp["Content-Type"], "image/jpeg")

    def test_author_profile_image_redirects_same_node_avatar(self):
        self.author.profileImage = "http://testserver/media/avatar.png"
        self.author.save(update_fields=["profileImage"])

        resp = self.client.get(f"/api/authors/{self.author.serial}/profile-image/")

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/media/avatar.png")
