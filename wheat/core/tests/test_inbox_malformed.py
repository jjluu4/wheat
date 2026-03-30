from rest_framework.test import APITestCase

from core.tests.factories import (
    build_author_payload,
    make_author,
    make_basic_auth_headers,
    make_entry,
    make_local_author,
    make_remote_node,
)


class InboxMalformedPayloadTests(APITestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="inbox-owner",
            display_name="Inbox Owner",
        )
        self.remote_node = make_remote_node(
            name="Malformed Partner",
            base_url="https://partner.example.com",
            api_base_url="https://partner.example.com/api",
            username="partner-user",
            password="partner-pass",
        )
        self.inbox_url = f"/api/authors/{self.owner.serial}/inbox"
        self.auth_headers = make_basic_auth_headers(
            self.remote_node.username,
            self.remote_node.password,
        )
        self.remote_author_payload = {
            "type": "author",
            "id": "https://partner.example.com/api/authors/remote-author",
            "host": "https://partner.example.com/api/",
            "displayName": "Remote Author",
            "github": "",
            "profileImage": "",
            "web": "https://partner.example.com/authors/remote-author/",
        }
        self.local_entry = make_entry(
            author=self.owner,
            title="Inbox target",
            content="target body",
            visibility="PUBLIC",
        )

    def test_inbox_rejects_missing_type_field(self):
        response = self.client.post(
            self.inbox_url,
            data={"author": self.remote_author_payload},
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Unsupported inbox object type")

    def test_inbox_rejects_unknown_type_field(self):
        response = self.client.post(
            self.inbox_url,
            data={"type": "share", "author": self.remote_author_payload},
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Unsupported inbox object type")

    def test_inbox_rejects_non_json_body(self):
        response = self.client.generic(
            "POST",
            self.inbox_url,
            data="not-json",
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)

    def test_inbox_rejects_entry_without_author_payload(self):
        response = self.client.post(
            self.inbox_url,
            data={
                "type": "entry",
                "id": "https://partner.example.com/api/authors/remote-author/entries/missing-author",
                "title": "Bad entry",
                "content": "body",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Author payload is required.")

    def test_inbox_rejects_author_payload_missing_required_fields(self):
        response = self.client.post(
            self.inbox_url,
            data={
                "type": "entry",
                "id": "https://partner.example.com/api/authors/remote-author/entries/bad-author-fields",
                "title": "Bad entry",
                "content": "body",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
                "author": {
                    "type": "author",
                    "id": "https://partner.example.com/api/authors/remote-author",
                    "host": "https://partner.example.com/api/",
                },
            },
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Author payload must include id, host, and displayName.",
        )

    def test_inbox_rejects_comment_with_missing_entry_target(self):
        response = self.client.post(
            self.inbox_url,
            data={
                "type": "comment",
                "id": "https://partner.example.com/api/authors/remote-author/commented/missing-entry",
                "comment": "hello",
                "contentType": "text/plain",
                "author": self.remote_author_payload,
            },
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Comment entry target not found")

    def test_inbox_rejects_like_without_object_target(self):
        response = self.client.post(
            self.inbox_url,
            data={
                "type": "like",
                "id": "https://partner.example.com/api/authors/remote-author/liked/no-object",
                "author": self.remote_author_payload,
            },
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Like object is required")

    def test_inbox_rejects_accept_without_actor_payload(self):
        response = self.client.post(
            self.inbox_url,
            data={
                "type": "accept",
                "object": build_author_payload(self.owner),
            },
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Author payload is required.")

    def test_inbox_put_rejects_non_entry_objects(self):
        response = self.client.put(
            self.inbox_url,
            data={
                "type": "comment",
                "id": "https://partner.example.com/api/authors/remote-author/commented/c1",
                "entry": self.local_entry.url,
                "comment": "updated",
                "contentType": "text/plain",
                "author": self.remote_author_payload,
            },
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"],
            "Only entry objects can be edited via inbox.",
        )

    def test_inbox_delete_rejects_non_entry_objects(self):
        remote_author = make_author(
            display_name="Remote Author",
            host="https://partner.example.com/api/",
            url=self.remote_author_payload["id"],
            web=self.remote_author_payload["web"],
        )
        like_target = make_entry(
            author=self.owner,
            title="Like target",
            content="body",
            visibility="PUBLIC",
        )

        response = self.client.delete(
            self.inbox_url,
            data={
                "type": "like",
                "id": f"{remote_author.url}/liked/delete-like",
                "object": like_target.url,
                "author": self.remote_author_payload,
            },
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"],
            "Only entry objects can be deleted via inbox.",
        )
