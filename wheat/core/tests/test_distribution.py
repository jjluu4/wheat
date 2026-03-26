import uuid
from unittest.mock import patch
import base64

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from core.models import Author, Follow, RemoteNode
from core.federation import send_to_author_inbox


class DistributionApiTests(APITestCase):
    def setUp(self):
        self.local_user = User.objects.create_user(username="local-dist", password="pass12345")
        self.local_author = Author.objects.create(
            user=self.local_user,
            serial=uuid.uuid4(),
            url="http://testserver/api/authors/local-dist",
            host="http://testserver/api/",
            displayName="Local Dist",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/local-dist",
        )
        self.remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://127.0.0.1:8001/api/authors/remote-author",
            host="http://127.0.0.1:8001/api/",
            displayName="Remote Author",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://127.0.0.1:8001/authors/remote-author",
        )
        RemoteNode.objects.create(
            name="remote-1",
            base_url="http://127.0.0.1:8001",
            api_base_url="http://127.0.0.1:8001/api",
            username="remote-user",
            password="remote-pass",
            is_active=True,
        )
        Follow.objects.create(actor=self.remote_author, target=self.local_author, status="ACCEPTED")
        self.entries_url = f"/api/authors/{self.local_author.serial}/entries/"

    @patch("core.federation.send_to_author_inbox")
    def test_public_entry_is_distributed_to_remote_follower(self, mock_send):
        mock_send.return_value = (True, None)
        self.client.login(username="local-dist", password="pass12345")

        response = self.client.post(
            self.entries_url,
            {
                "title": "Public dist",
                "content": "hello",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(mock_send.call_count, 1)

    @patch("core.federation.send_to_author_inbox")
    def test_friends_entry_not_distributed_when_not_mutual(self, mock_send):
        mock_send.return_value = (True, None)
        self.client.login(username="local-dist", password="pass12345")

        response = self.client.post(
            self.entries_url,
            {
                "title": "Friends dist",
                "content": "hello",
                "contentType": "text/plain",
                "visibility": "FRIENDS",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(mock_send.call_count, 0)

    @patch("core.federation.logger")
    @patch("core.federation.send_to_author_inbox")
    def test_public_entry_distribution_failure_logs_and_does_not_crash(self, mock_send, mock_logger):
        mock_send.return_value = (False, "inbox rejected")
        self.client.login(username="local-dist", password="pass12345")

        response = self.client.post(
            self.entries_url,
            {
                "title": "Public dist fail",
                "content": "hello",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(mock_send.call_count, 1)
    @patch("core.helpers.requests.post")
    def test_send_to_author_inbox_uses_fqid_derived_inbox_url(self, mock_post):
        mock_post.return_value.status_code = 201

        ok, error = send_to_author_inbox(self.remote_author, {"type": "entry"}, method="POST")

        self.assertTrue(ok)
        self.assertIsNone(error)
        mock_post.assert_called_once()
        self.assertEqual(
            mock_post.call_args.args[0],
            "http://127.0.0.1:8001/api/authors/remote-author/inbox",
        )
        self.assertEqual(mock_post.call_args.kwargs["json"], {"type": "entry"})
        auth_header = mock_post.call_args.kwargs["headers"]["Authorization"]
        self.assertEqual(
            auth_header,
            f"Basic {base64.b64encode(b'remote-user:remote-pass').decode('utf-8')}",
        )
