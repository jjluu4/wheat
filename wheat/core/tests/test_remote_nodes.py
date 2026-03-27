from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from core.federation import sync_remote_authors_and_public_entries
from core.models import Author, RemoteNode


User = get_user_model()


class RemoteNodeViewTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff-user",
            password="pass12345",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="regular-user",
            password="pass12345",
        )
        self.node = RemoteNode.objects.create(
            name="Partner Node",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="partner-user",
            password="partner-pass",
            is_active=True,
            notes="Primary partner",
        )

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse("remote_node_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_non_staff_user_gets_403_for_staff_views(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("remote_node_list"))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse("remote_node_add"))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse("remote_node_edit", args=[self.node.pk]))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse("remote_node_toggle", args=[self.node.pk]))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse("remote_node_sync"))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_view_remote_node_pages(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("remote_node_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Partner Node")

        response = self.client.get(reverse("remote_node_add"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("remote_node_edit", args=[self.node.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "partner-user")

    def test_staff_can_create_remote_node_with_required_fields(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("remote_node_add"),
            data={
                "name": "",
                "base_url": "https://new-node.example.com/",
                "api_base_url": "",
                "username": "new-user",
                "password": "new-pass",
                "is_active": "on",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)

        node = RemoteNode.objects.get(base_url="https://new-node.example.com")
        self.assertEqual(node.api_base_url, "https://new-node.example.com/api")
        self.assertEqual(node.username, "new-user")
        self.assertEqual(node.password, "new-pass")
        self.assertTrue(node.is_active)

    def test_duplicate_normalized_base_url_is_rejected(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("remote_node_add"),
            data={
                "name": "Duplicate",
                "base_url": "https://partner.example.com/",
                "api_base_url": "",
                "username": "another-user",
                "password": "another-pass",
                "is_active": "on",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A remote node with this base URL already exists.")
        self.assertEqual(RemoteNode.objects.count(), 1)

    def test_edit_remote_node_preserves_password_when_blank(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("remote_node_edit", args=[self.node.pk]),
            data={
                "name": "Updated Node",
                "base_url": "https://partner.example.com/",
                "api_base_url": "",
                "username": "updated-user",
                "password": "",
                "is_active": "on",
                "notes": "Updated notes",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.node.refresh_from_db()
        self.assertEqual(self.node.name, "Updated Node")
        self.assertEqual(self.node.base_url, "https://partner.example.com")
        self.assertEqual(self.node.api_base_url, "https://partner.example.com/api")
        self.assertEqual(self.node.username, "updated-user")
        self.assertEqual(self.node.password, "partner-pass")

    def test_edit_remote_node_replaces_password_when_provided(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("remote_node_edit", args=[self.node.pk]),
            data={
                "name": "Partner Node",
                "base_url": "https://partner.example.com",
                "api_base_url": "https://partner.example.com/custom-api/",
                "username": "partner-user",
                "password": "new-secret",
                "notes": "Primary partner",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.node.refresh_from_db()
        self.assertEqual(self.node.api_base_url, "https://partner.example.com/custom-api")
        self.assertEqual(self.node.password, "new-secret")
        self.assertFalse(self.node.is_active)

    def test_toggle_remote_node_flips_active_flag(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("remote_node_toggle", args=[self.node.pk]))
        self.assertEqual(response.status_code, 302)

        self.node.refresh_from_db()
        self.assertFalse(self.node.is_active)

    def test_toggle_route_rejects_get(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("remote_node_toggle", args=[self.node.pk]))
        self.assertEqual(response.status_code, 405)

    @patch("core.views.remote_node_views.sync_remote_authors_and_public_entries")
    def test_staff_can_sync_remote_authors(self, mock_sync):
        mock_sync.return_value = {"authors": 3, "entries": 5}
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("remote_node_sync"))
        self.assertEqual(response.status_code, 302)
        mock_sync.assert_called_once()

    def test_sync_route_rejects_get(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("remote_node_sync"))
        self.assertEqual(response.status_code, 405)

    def test_staff_nav_shows_manage_nodes_link(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("author_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manage Nodes")

    def test_non_staff_nav_hides_manage_nodes_link(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("author_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Manage Nodes")


class RemoteNodeSyncTests(TestCase):
    def setUp(self):
        self.node = RemoteNode.objects.create(
            name="Partner Node",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="partner-user",
            password="partner-pass",
            is_active=True,
        )

    @staticmethod
    def author_payload(author_id, display_name):
        return {
            "type": "author",
            "id": f"https://partner.example.com/api/authors/{author_id}",
            "host": "https://partner.example.com/api",
            "displayName": display_name,
            "github": "",
            "profileImage": "https://placehold.co/60x60.png",
            "web": f"https://partner.example.com/authors/{author_id}",
        }

    @staticmethod
    def entry_payload(author_id, entry_id, visibility="PUBLIC"):
        return {
            "type": "entry",
            "id": f"https://partner.example.com/api/authors/{author_id}/entries/{entry_id}",
            "title": f"Entry {entry_id}",
            "content": f"Body {entry_id}",
            "contentType": "text/plain",
            "visibility": visibility,
            "author": RemoteNodeSyncTests.author_payload(author_id, f"Remote {author_id}"),
        }

    def test_sync_walks_all_author_and_entry_pages(self):
        fetch_calls = []

        def fake_fetch(url, remote_node, timeout=10):
            fetch_calls.append(url)
            parsed = urlparse(url)
            page = parse_qs(parsed.query).get("page", ["1"])[0]

            if parsed.path == "/api/authors":
                if page == "1":
                    return {"authors": [self.author_payload("author-1", "Remote One")]}
                if page == "2":
                    return {"authors": [self.author_payload("author-2", "Remote Two")]}
                return {"authors": []}

            if parsed.path == "/api/authors/author-1/entries/":
                if page == "1":
                    return {"entries": [self.entry_payload("author-1", "entry-1")]}
                if page == "2":
                    return {"entries": [self.entry_payload("author-1", "entry-2")]}
                return {"entries": []}

            if parsed.path == "/api/authors/author-2/entries/":
                if page == "1":
                    return {"entries": [self.entry_payload("author-2", "entry-3")]}
                return {"entries": []}

            return None

        created_entry_urls = []

        def fake_create_or_update(entry_payload, author):
            created_entry_urls.append(entry_payload["id"])
            return object()

        with patch("core.federation.fetch_remote_json", side_effect=fake_fetch):
            with patch("core.federation.create_or_update_entry_from_remote_payload", side_effect=fake_create_or_update):
                result = sync_remote_authors_and_public_entries()

        self.assertEqual(result, {"authors": 2, "entries": 3})
        self.assertEqual(
            set(Author.objects.values_list("url", flat=True)),
            {
                "https://partner.example.com/api/authors/author-1",
                "https://partner.example.com/api/authors/author-2",
            },
        )
        self.assertEqual(
            created_entry_urls,
            [
                "https://partner.example.com/api/authors/author-1/entries/entry-1",
                "https://partner.example.com/api/authors/author-1/entries/entry-2",
                "https://partner.example.com/api/authors/author-2/entries/entry-3",
            ],
        )
        self.assertIn("https://partner.example.com/api/authors?page=1&size=100", fetch_calls)
        self.assertIn("https://partner.example.com/api/authors?page=2&size=100", fetch_calls)
        self.assertIn("https://partner.example.com/api/authors/author-1/entries/?page=1&size=100", fetch_calls)
        self.assertIn("https://partner.example.com/api/authors/author-1/entries/?page=2&size=100", fetch_calls)
        self.assertIn("https://partner.example.com/api/authors/author-2/entries/?page=1&size=100", fetch_calls)

    def test_sync_imports_only_public_entries(self):
        def fake_fetch(url, remote_node, timeout=10):
            parsed = urlparse(url)
            page = parse_qs(parsed.query).get("page", ["1"])[0]

            if parsed.path == "/api/authors":
                if page == "1":
                    return {"authors": [self.author_payload("author-1", "Remote One")]}
                return {"authors": []}

            if parsed.path == "/api/authors/author-1/entries/":
                if page == "1":
                    return {
                        "entries": [
                            self.entry_payload("author-1", "public-entry", "PUBLIC"),
                            self.entry_payload("author-1", "unlisted-entry", "UNLISTED"),
                            self.entry_payload("author-1", "friends-entry", "FRIENDS"),
                            self.entry_payload("author-1", "deleted-entry", "DELETED"),
                        ]
                    }
                return {"entries": []}

            return None

        created_entry_urls = []

        def fake_create_or_update(entry_payload, author):
            created_entry_urls.append(entry_payload["id"])
            return object()

        with patch("core.federation.fetch_remote_json", side_effect=fake_fetch):
            with patch("core.federation.create_or_update_entry_from_remote_payload", side_effect=fake_create_or_update):
                result = sync_remote_authors_and_public_entries()

        self.assertEqual(result, {"authors": 1, "entries": 1})
        self.assertEqual(
            created_entry_urls,
            ["https://partner.example.com/api/authors/author-1/entries/public-entry"],
        )
