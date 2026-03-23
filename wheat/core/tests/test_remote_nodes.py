from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import RemoteNode


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
