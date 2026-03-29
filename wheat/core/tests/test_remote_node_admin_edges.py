from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from core.admin import approve_pending_users
from core.models import Author, RemoteNode
from core.tests.factories import make_local_author


class RemoteNodeAuthorsApiEdgeTests(APITestCase):
    def setUp(self):
        self.user, self.author = make_local_author(
            username="remote-node-api-user",
            display_name="Remote Node API User",
        )
        self.active_node = RemoteNode.objects.create(
            name="Active Node",
            base_url="https://active.example.com",
            api_base_url="https://active.example.com/api",
            username="active-user",
            password="active-pass",
            is_active=True,
        )
        self.inactive_node = RemoteNode.objects.create(
            name="Inactive Node",
            base_url="https://inactive.example.com",
            api_base_url="https://inactive.example.com/api",
            username="inactive-user",
            password="inactive-pass",
            is_active=False,
        )

    def test_remote_node_authors_returns_404_for_inactive_node(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api_remote_node_authors", args=[self.inactive_node.pk]))

        self.assertEqual(response.status_code, 404)

    @patch("core.apis.author_api.fetch_remote_authors_page")
    def test_remote_node_authors_returns_502_for_upstream_error(self, mock_fetch):
        mock_fetch.return_value = {
            "authors": [],
            "has_more": False,
            "error": "remote catalog failed",
        }
        self.client.force_login(self.user)

        response = self.client.get(
            f"{reverse('api_remote_node_authors', args=[self.active_node.pk])}?page=2&size=7"
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"], "remote catalog failed")
        mock_fetch.assert_called_once_with(self.active_node, 2, 7)


class AdminApprovalEdgeTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.staff_user = User.objects.create_user(
            username="approval-staff",
            password="pass12345",
            is_staff=True,
            is_active=True,
        )
        self.request = self.factory.get("/", HTTP_HOST="testserver")
        self.request.user = self.staff_user

    def test_approve_pending_users_does_not_duplicate_existing_author(self):
        active_user = User.objects.create_user(
            username="already-approved",
            password="pass12345",
            is_active=True,
        )
        author = Author.objects.create(
            user=active_user,
            displayName="already-approved",
            serial="11111111-1111-1111-1111-111111111111",
            url="http://testserver/api/authors/11111111-1111-1111-1111-111111111111",
            host="http://testserver/api/",
            web="http://testserver/authors/11111111-1111-1111-1111-111111111111/",
        )

        approve_pending_users(None, self.request, User.objects.filter(pk=active_user.pk))

        self.assertEqual(Author.objects.filter(user=active_user).count(), 1)
        self.assertEqual(Author.objects.get(user=active_user).pk, author.pk)

    def test_approve_pending_users_handles_multiple_users_in_one_batch(self):
        first = User.objects.create_user(
            username="batch-one",
            password="pass12345",
            is_active=False,
        )
        second = User.objects.create_user(
            username="batch-two",
            password="pass12345",
            is_active=False,
        )

        approve_pending_users(None, self.request, User.objects.filter(pk__in=[first.pk, second.pk]))

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertTrue(first.is_active)
        self.assertTrue(second.is_active)
        self.assertTrue(Author.objects.filter(user=first).exists())
        self.assertTrue(Author.objects.filter(user=second).exists())
        self.assertEqual(Author.objects.filter(user__in=[first, second]).count(), 2)
