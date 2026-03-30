from rest_framework.test import APITestCase

from core.models import Entry, EntryLike, Follow, InboxItem
from core.tests.factories import (
    build_author_payload,
    make_basic_auth_headers,
    make_entry,
    make_local_author,
    make_remote_node,
)


class InboxIdempotencyAndOrderingTests(APITestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="inbox-order-owner",
            display_name="Inbox Ordering Owner",
        )
        self.remote_node = make_remote_node(
            name="Ordering Partner",
            base_url="https://ordering.example.com",
            api_base_url="https://ordering.example.com/api",
            username="ordering-user",
            password="ordering-pass",
        )
        self.auth_headers = make_basic_auth_headers(
            self.remote_node.username,
            self.remote_node.password,
        )
        self.inbox_url = f"/api/authors/{self.owner.serial}/inbox"
        self.remote_author_payload = {
            "type": "author",
            "id": "https://ordering.example.com/api/authors/remote-author",
            "host": "https://ordering.example.com/api/",
            "displayName": "Ordering Remote Author",
            "github": "",
            "profileImage": "",
            "web": "https://ordering.example.com/authors/remote-author/",
        }
        self.local_entry = make_entry(
            author=self.owner,
            title="Local target",
            content="local target body",
            visibility="PUBLIC",
        )

    def test_inbox_put_same_entry_event_is_idempotent(self):
        payload = {
            "type": "entry",
            "id": "https://ordering.example.com/api/authors/remote-author/entries/put-entry",
            "title": "Put entry",
            "content": "put body",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "author": self.remote_author_payload,
        }

        first = self.client.put(self.inbox_url, data=payload, format="json", **self.auth_headers)
        second = self.client.put(self.inbox_url, data=payload, format="json", **self.auth_headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Entry.objects.filter(url=payload["id"]).count(), 1)
        self.assertEqual(InboxItem.objects.filter(owner=self.owner, item_type="entry").count(), 1)
        self.assertEqual(second.json()["status"], "already-processed")

    def test_inbox_delete_same_entry_event_is_idempotent(self):
        payload = {
            "type": "entry",
            "id": "https://ordering.example.com/api/authors/remote-author/entries/delete-entry",
            "title": "Delete entry",
            "content": "delete me",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "author": self.remote_author_payload,
        }
        create_response = self.client.post(
            self.inbox_url,
            data=payload,
            format="json",
            **self.auth_headers,
        )
        self.assertEqual(create_response.status_code, 201)

        first = self.client.delete(self.inbox_url, data=payload, format="json", **self.auth_headers)
        second = self.client.delete(self.inbox_url, data=payload, format="json", **self.auth_headers)

        self.assertEqual(first.status_code, 204)
        self.assertEqual(second.status_code, 200)
        entry = Entry.objects.get(url=payload["id"])
        self.assertEqual(entry.visibility, "DELETED")
        self.assertEqual(InboxItem.objects.filter(owner=self.owner, item_type="entry").count(), 2)
        self.assertEqual(second.json()["status"], "already-processed")

    def test_inbox_reposting_same_unlike_event_is_idempotent(self):
        like_payload = {
            "type": "like",
            "id": "https://ordering.example.com/api/authors/remote-author/liked/like-1",
            "object": self.local_entry.url,
            "author": self.remote_author_payload,
        }
        unlike_payload = {
            "type": "unlike",
            "id": "https://ordering.example.com/api/authors/remote-author/unlikes/unlike-1",
            "object": self.local_entry.url,
            "author": self.remote_author_payload,
        }

        like_response = self.client.post(
            self.inbox_url,
            data=like_payload,
            format="json",
            **self.auth_headers,
        )
        self.assertEqual(like_response.status_code, 201)
        self.assertEqual(EntryLike.objects.filter(entry=self.local_entry).count(), 1)

        first = self.client.post(
            self.inbox_url,
            data=unlike_payload,
            format="json",
            **self.auth_headers,
        )
        second = self.client.post(
            self.inbox_url,
            data=unlike_payload,
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(EntryLike.objects.filter(entry=self.local_entry).count(), 0)
        self.assertEqual(
            InboxItem.objects.filter(owner=self.owner, item_id=unlike_payload["id"]).count(),
            1,
        )

    def test_inbox_delete_before_create_applies_later_create_payload_current_behavior(self):
        payload = {
            "type": "entry",
            "id": "https://ordering.example.com/api/authors/remote-author/entries/out-of-order-entry",
            "title": "Out of order",
            "content": "final body",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "author": self.remote_author_payload,
        }

        delete_response = self.client.delete(
            self.inbox_url,
            data=payload,
            format="json",
            **self.auth_headers,
        )
        create_response = self.client.post(
            self.inbox_url,
            data=payload,
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(create_response.status_code, 201)
        entry = Entry.objects.get(url=payload["id"])
        self.assertEqual(entry.visibility, "PUBLIC")
        self.assertEqual(entry.content, "final body")
        self.assertEqual(InboxItem.objects.filter(owner=self.owner, item_type="entry").count(), 2)

    def test_accept_before_follow_exists_creates_accepted_follow_current_behavior(self):
        payload = {
            "type": "accept",
            "id": "https://ordering.example.com/api/accepts/accept-before-follow",
            "actor": self.remote_author_payload,
            "object": build_author_payload(self.owner),
        }

        response = self.client.post(
            self.inbox_url,
            data=payload,
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 201)
        follow = Follow.objects.get(target__url=self.remote_author_payload["id"], actor=self.owner)
        self.assertEqual(follow.status, "ACCEPTED")

    def test_unlike_before_like_exists_returns_removed_and_records_event(self):
        payload = {
            "type": "unlike",
            "id": "https://ordering.example.com/api/authors/remote-author/unlikes/unlike-before-like",
            "object": self.local_entry.url,
            "author": self.remote_author_payload,
        }

        response = self.client.post(
            self.inbox_url,
            data=payload,
            format="json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "removed")
        self.assertEqual(EntryLike.objects.filter(entry=self.local_entry).count(), 0)
        self.assertEqual(InboxItem.objects.filter(owner=self.owner, item_id=payload["id"]).count(), 1)
