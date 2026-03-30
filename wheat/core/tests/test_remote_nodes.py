import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from core.helpers import build_paginated_remote_authors_url, resolved_remote_api_base
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

    def test_unauthenticated_user_redirected_to_login_for_delete(self):
        response = self.client.get(reverse("remote_node_delete", args=[self.node.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

        response = self.client.post(reverse("remote_node_delete", args=[self.node.pk]))
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

        response = self.client.get(reverse("remote_node_delete", args=[self.node.pk]))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse("remote_node_delete", args=[self.node.pk]))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse("fetch_remote_node_authors_page", args=[self.node.pk]))
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
        response = self.client.post(
            reverse("remote_node_toggle", args=[self.node.pk]),
            data={"target_state": "disable"},
        )
        self.assertEqual(response.status_code, 302)

        self.node.refresh_from_db()
        self.assertFalse(self.node.is_active)

    def test_toggle_remote_node_to_same_state_is_idempotent(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("remote_node_toggle", args=[self.node.pk]),
            data={"target_state": "enable"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.node.refresh_from_db()
        self.assertTrue(self.node.is_active)

    def test_toggle_remote_node_with_invalid_target_state_leaves_state_unchanged(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("remote_node_toggle", args=[self.node.pk]),
            data={"target_state": "maybe"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.node.refresh_from_db()
        self.assertTrue(self.node.is_active)
        self.assertContains(response, "Invalid remote node toggle request.")

    def test_toggle_route_rejects_get(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("remote_node_toggle", args=[self.node.pk]))
        self.assertEqual(response.status_code, 405)

    def test_staff_can_view_delete_confirmation_page(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("remote_node_delete", args=[self.node.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete Remote Node")
        self.assertContains(response, "Partner Node")
        self.assertContains(response, "https://partner.example.com")
        self.assertContains(response, "partner-user")

    def test_delete_confirmation_get_does_not_remove_node(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("remote_node_delete", args=[self.node.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(RemoteNode.objects.filter(pk=self.node.pk).exists())

    def test_staff_can_delete_remote_node(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("remote_node_delete", args=[self.node.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("remote_node_list"))
        self.assertFalse(RemoteNode.objects.filter(pk=self.node.pk).exists())

    def test_delete_only_removes_target_node(self):
        other_node = RemoteNode.objects.create(
            name="Other Node",
            base_url="https://other.example.com",
            api_base_url="https://other.example.com/api",
            username="other-user",
            password="other-pass",
            is_active=False,
            notes="Secondary partner",
        )
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("remote_node_delete", args=[self.node.pk]))
        self.assertEqual(response.status_code, 302)

        self.assertFalse(RemoteNode.objects.filter(pk=self.node.pk).exists())
        self.assertTrue(RemoteNode.objects.filter(pk=other_node.pk).exists())

    def test_delete_nonexistent_node_returns_404(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("remote_node_delete", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_deleted_node_no_longer_appears_in_list(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("remote_node_delete", args=[self.node.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Partner Node")

    def test_remote_node_clean_adds_api_when_api_base_is_site_root_only(self):
        node = RemoteNode(
            base_url="http://127.0.0.1:9001",
            api_base_url="http://127.0.0.1:9001",
            username="u",
            password="p",
        )
        node.full_clean()
        self.assertEqual(node.api_base_url, "http://127.0.0.1:9001/api")

    def test_resolved_remote_api_base_targets_api_authors_not_html_list(self):
        node = RemoteNode(
            base_url="http://127.0.0.1:9002",
            api_base_url="http://127.0.0.1:9002",
            username="u",
            password="p",
        )
        api_root = resolved_remote_api_base(node)
        self.assertEqual(api_root, "http://127.0.0.1:9002/api")
        url = build_paginated_remote_authors_url(api_root, 1, 5)
        self.assertIn("127.0.0.1:9002/api/authors/", url)

    @patch("core.views.author_views.fetch_remote_authors_catalog_page")
    def test_staff_nav_shows_manage_nodes_link(self, mock_catalog):
        mock_catalog.return_value = {
            "error": None,
            "authors": [
                {
                    "displayName": "Remote Author",
                    "web": "https://partner.example.com/authors/ra",
                    "id": "https://partner.example.com/api/authors/ra",
                    "profileImage": "",
                }
            ],
            "page": 1,
            "page_size": 5,
            "total_count": 6,
            "has_next": True,
            "num_pages": 2,
        }
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("author_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manage Nodes")
        self.assertContains(response, "Partner Node")
        self.assertContains(response, "Remote Author")

    @patch("core.views.author_views.fetch_remote_authors_catalog_page")
    def test_non_staff_nav_hides_manage_nodes_link(self, mock_catalog):
        mock_catalog.return_value = {
            "error": None,
            "authors": [],
            "page": 1,
            "page_size": 5,
            "total_count": 0,
            "has_next": False,
            "num_pages": 1,
        }
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("author_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Manage Nodes")
        self.assertContains(response, "Partner Node")

    @patch("core.views.remote_node_views.fetch_remote_authors_page")
    def test_staff_fetch_remote_authors_page_redirects(self, mock_fetch):
        mock_fetch.return_value = {
            "upserted": 1,
            "authors": [],
            "has_more": False,
            "error": None,
            "item_count": 3,
            "page": 1,
            "page_size": 5,
        }
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("fetch_remote_node_authors_page", args=[self.node.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("author_list"))
        mock_fetch.assert_called_once()
        self.assertEqual(mock_fetch.call_args[0][1], 1)
        self.assertEqual(mock_fetch.call_args[0][2], 5)

    @patch("core.views.remote_node_views.fetch_remote_authors_page")
    def test_fetch_next_advances_session_per_node(self, mock_fetch):
        mock_fetch.side_effect = [
            {
                "upserted": 5,
                "authors": [],
                "has_more": True,
                "error": None,
                "item_count": 5,
                "page": 1,
                "page_size": 5,
            },
            {
                "upserted": 2,
                "authors": [],
                "has_more": False,
                "error": None,
                "item_count": 2,
                "page": 2,
                "page_size": 5,
            },
        ]
        self.client.force_login(self.staff_user)
        url = reverse("fetch_remote_node_authors_page", args=[self.node.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(mock_fetch.call_args_list[0][0][1], 1)
        self.assertEqual(mock_fetch.call_args_list[1][0][1], 2)


class RemoteNodeAuthorsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api-user", password="pass12345")
        self.node = RemoteNode.objects.create(
            name="Partner",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="u",
            password="p",
            is_active=True,
        )

    def test_remote_node_authors_requires_login(self):
        url = reverse("api_remote_node_authors", args=[self.node.pk])
        resp = self.client.get(f"{url}?page=1&size=5")
        self.assertEqual(resp.status_code, 401)

    @patch("core.apis.author_api.fetch_remote_authors_page")
    def test_remote_node_authors_proxies_when_authenticated(self, mock_fetch):
        author = Author.objects.create(
            displayName="FromRemote",
            serial=uuid.uuid4(),
            url="https://partner.example.com/api/authors/x",
            host="https://partner.example.com/api/",
            web="https://partner.example.com/authors/x",
        )
        mock_fetch.return_value = {
            "upserted": 1,
            "authors": [author],
            "has_more": True,
            "error": None,
        }
        self.client.force_login(self.user)
        url = reverse("api_remote_node_authors", args=[self.node.pk])
        resp = self.client.get(f"{url}?page=1&size=5")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "authors")
        self.assertEqual(len(resp.data["authors"]), 1)
        self.assertTrue(resp.data["has_more"])
        mock_fetch.assert_called_once()
