from unittest.mock import Mock, patch

from rest_framework.test import APITestCase

from core.tests.factories import make_basic_auth_headers, make_entry, make_local_author, make_remote_node


class AuthBoundaryRegressionTests(APITestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="boundary-owner",
            display_name="Boundary Owner",
        )
        self.remote_node = make_remote_node(
            name="Boundary Partner",
            base_url="https://boundary.example.com",
            api_base_url="https://boundary.example.com/api",
            username="boundary-user",
            password="boundary-pass",
        )
        self.remote_headers = make_basic_auth_headers(
            self.remote_node.username,
            self.remote_node.password,
        )
        self.entry = make_entry(
            author=self.owner,
            title="Boundary entry",
            content="boundary body",
            visibility="PUBLIC",
        )

    def test_remote_basic_auth_cannot_update_local_author_profile(self):
        response = self.client.put(
            f"/api/authors/{self.owner.serial}/",
            data={"displayName": "Remote should fail"},
            format="json",
            **self.remote_headers,
        )

        self.assertEqual(response.status_code, 401)

    def test_remote_basic_auth_cannot_create_local_entry(self):
        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "title": "Remote should fail",
                "content": "body",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
            **self.remote_headers,
        )

        self.assertEqual(response.status_code, 401)

    def test_remote_basic_auth_cannot_access_local_following_list(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/following",
            **self.remote_headers,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Invalid username/password.")

    def test_local_session_auth_cannot_post_to_inbox_without_remote_basic_auth(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            f"/api/authors/{self.owner.serial}/inbox",
            data={
                "type": "entry",
                "id": "https://boundary.example.com/api/authors/remote-author/entries/e1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], 'Basic realm="Node to Node API"')

    def test_inbox_rejects_non_basic_authorization_scheme(self):
        response = self.client.post(
            f"/api/authors/{self.owner.serial}/inbox",
            data={
                "type": "entry",
                "id": "https://boundary.example.com/api/authors/remote-author/entries/e1",
            },
            format="json",
            HTTP_AUTHORIZATION="Bearer totally-not-basic",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], 'Basic realm="Node to Node API"')

    def test_image_proxy_rejects_inactive_remote_node_host(self):
        self.remote_node.is_active = False
        self.remote_node.save(update_fields=["is_active"])

        response = self.client.get(
            "/api/media/image-proxy/",
            {"url": "https://boundary.example.com/media/avatar.png"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Image URL is not allowlisted.")

    @patch("core.helpers.requests.get")
    def test_image_proxy_rejects_remote_non_image_content(self, mock_get):
        mock_response = Mock(status_code=200, content=b"not-image")
        mock_response.headers = {"Content-Type": "text/html"}
        mock_get.return_value = mock_response

        response = self.client.get(
            "/api/media/image-proxy/",
            {"url": "https://boundary.example.com/media/not-image"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"], "Remote resource is not an image.")
