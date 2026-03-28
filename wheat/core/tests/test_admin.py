import uuid

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from core.admin import approve_pending_users, create_local_author_if_missing
from core.models import Author


class AdminApprovalTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.staff_user = User.objects.create_user(
            username="staff-admin",
            password="pass12345",
            is_staff=True,
            is_active=True,
        )

    def test_approve_pending_users_creates_author_and_exposes_user_via_authors_api(self):
        pending_user = User.objects.create_user(
            username="pending-user",
            password="pass12345",
            is_active=False,
        )
        self.assertFalse(hasattr(pending_user, "author_profile"))

        request = self.factory.get("/", HTTP_HOST="testserver")
        request.user = self.staff_user

        approve_pending_users(None, request, User.objects.filter(pk=pending_user.pk))

        pending_user.refresh_from_db()
        self.assertTrue(pending_user.is_active)

        author = Author.objects.get(user=pending_user)
        self.assertEqual(author.displayName, "pending-user")
        self.assertEqual(author.host, "http://testserver/api/")
        self.assertEqual(author.url, f"http://testserver/api/authors/{author.serial}")
        self.assertEqual(author.web, f"http://testserver/authors/{author.serial}/")

        response = self.client.get("/api/authors/")
        self.assertEqual(response.status_code, 200)
        author_ids = {item["id"] for item in response.data["authors"]}
        self.assertIn(author.url, author_ids)

    def test_create_local_author_if_missing_is_idempotent(self):
        request = self.factory.get("/", HTTP_HOST="testserver")
        request.user = self.staff_user
        u = User.objects.create_user(username="solo-active", password="pass12345", is_active=True)
        self.assertFalse(Author.objects.filter(user=u).exists())

        create_local_author_if_missing(request, u)
        self.assertEqual(Author.objects.filter(user=u).count(), 1)
        create_local_author_if_missing(request, u)
        self.assertEqual(Author.objects.filter(user=u).count(), 1)

