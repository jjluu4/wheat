from rest_framework.test import APITestCase
from django.contrib.auth.models import User
import base64
import uuid

from core.models import Author, Entry, RemoteNode


class InboxAuthTests(APITestCase):
    def setUp(self):
        self.local_user = User.objects.create_user(username="local-owner", password="pass12345")
        self.local_author = Author.objects.create(
            user=self.local_user,
            displayName="Local Owner",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
            host="http://testserver/api/",
            web=f"http://testserver/authors/{uuid.uuid4()}/",
        )
        self.remote_node = RemoteNode.objects.create(
            name="Partner Node",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="partner-user",
            password="partner-pass",
            is_active=True,
        )
        self.inbox_url = f"/api/authors/{self.local_author.serial}/inbox"
        self.remote_author_id = "https://partner.example.com/api/authors/remote-author"
        self.entry_id = f"{self.remote_author_id}/entries/remote-entry"
        self.entry_payload = {
            "type": "entry",
            "id": self.entry_id,
            "title": "Remote Post",
            "content": "Remote content",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "author": {
                "type": "author",
                "id": self.remote_author_id,
                "host": "https://partner.example.com/api/",
                "displayName": "Remote Author",
                "web": "https://partner.example.com/authors/remote-author",
            },
        }

    def _basic_auth_header(self, username=None, password=None):
        username = username or self.remote_node.username
        password = password or self.remote_node.password
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        return f"Basic {encoded}"

    def test_inbox_post_requires_basic_auth(self):
        response = self.client.post(self.inbox_url, data=self.entry_payload, format="json")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], 'Basic realm="Node to Node API"')
        self.assertFalse(Author.objects.filter(url=self.remote_author_id).exists())
        self.assertFalse(Entry.objects.filter(url=self.entry_id).exists())

    def test_inbox_post_rejects_malformed_basic_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="Basic not-base64")

        response = self.client.post(self.inbox_url, data=self.entry_payload, format="json")

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Author.objects.filter(url=self.remote_author_id).exists())
        self.assertFalse(Entry.objects.filter(url=self.entry_id).exists())

    def test_inbox_post_rejects_wrong_credentials(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._basic_auth_header(password="wrong-pass"))

        response = self.client.post(self.inbox_url, data=self.entry_payload, format="json")

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Author.objects.filter(url=self.remote_author_id).exists())
        self.assertFalse(Entry.objects.filter(url=self.entry_id).exists())

    def test_inbox_post_rejects_inactive_remote_node(self):
        self.remote_node.is_active = False
        self.remote_node.save(update_fields=["is_active"])
        self.client.credentials(HTTP_AUTHORIZATION=self._basic_auth_header())

        response = self.client.post(self.inbox_url, data=self.entry_payload, format="json")

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Author.objects.filter(url=self.remote_author_id).exists())
        self.assertFalse(Entry.objects.filter(url=self.entry_id).exists())

    def test_inbox_post_rejects_payload_from_other_node(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._basic_auth_header())
        payload = {
            **self.entry_payload,
            "author": {
                **self.entry_payload["author"],
                "id": "https://other.example.com/api/authors/remote-author",
                "host": "https://other.example.com/api/",
            },
        }

        response = self.client.post(self.inbox_url, data=payload, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Author.objects.filter(url=payload["author"]["id"]).exists())
        self.assertFalse(Entry.objects.filter(url=self.entry_id).exists())

    def test_inbox_post_with_valid_basic_auth_creates_entry(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._basic_auth_header())

        response = self.client.post(self.inbox_url, data=self.entry_payload, format="json")

        self.assertEqual(response.status_code, 201)
        remote_author = Author.objects.get(url=self.remote_author_id)
        entry = Entry.objects.get(url=self.entry_id)
        self.assertEqual(entry.author, remote_author)
        self.assertEqual(entry.content, "Remote content")
        self.assertEqual(entry.visibility, "PUBLIC")

    def test_inbox_delete_with_valid_basic_auth_marks_entry_deleted(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._basic_auth_header())
        create_response = self.client.post(self.inbox_url, data=self.entry_payload, format="json")
        self.assertEqual(create_response.status_code, 201)

        delete_payload = {
            **self.entry_payload,
            "content": "Remote content updated",
        }
        delete_response = self.client.delete(self.inbox_url, data=delete_payload, format="json")

        self.assertEqual(delete_response.status_code, 204)
        entry = Entry.objects.get(url=self.entry_id)
        self.assertEqual(entry.visibility, "DELETED")

    def test_inbox_delete_requires_basic_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._basic_auth_header())
        create_response = self.client.post(self.inbox_url, data=self.entry_payload, format="json")
        self.assertEqual(create_response.status_code, 201)
        self.client.credentials()

        delete_response = self.client.delete(self.inbox_url, data=self.entry_payload, format="json")

        self.assertEqual(delete_response.status_code, 401)
        entry = Entry.objects.get(url=self.entry_id)
        self.assertEqual(entry.visibility, "PUBLIC")


class LocalApiRegressionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.author = Author.objects.create(
            user=self.user,
            displayName="Owner",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
            host="http://testserver/api/",
            web=f"http://testserver/authors/{uuid.uuid4()}/",
        )

    def test_local_session_author_update_still_works(self):
        self.client.login(username="owner", password="pass12345")

        response = self.client.put(
            f"/api/authors/{self.author.serial}/",
            data={"displayName": "Updated Owner"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, "Updated Owner")

    def test_local_session_entry_create_still_works(self):
        self.client.login(username="owner", password="pass12345")

        response = self.client.post(
            f"/api/authors/{self.author.serial}/entries/",
            data={
                "content": "Local API entry",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Entry.objects.filter(author=self.author, content="Local API entry").exists())
