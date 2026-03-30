import base64
import uuid

from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from rest_framework.test import APITestCase

from core.models import Author, Comment, CommentLike, Entry, EntryLike, Follow, InboxItem, RemoteNode


def basic_auth_value(username, password):
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


class InboxApiTests(APITestCase):
    def setUp(self):
        self.owner_user = User.objects.create_user(username="owner-inbox", password="pass12345")
        self.owner = Author.objects.create(
            user=self.owner_user,
            serial=uuid.uuid4(),
            url="http://testserver/api/authors/owner-inbox",
            host="http://testserver/api/",
            displayName="Owner Inbox",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/owner-inbox",
        )
        self.remote_node = RemoteNode.objects.create(
            name="remote-a",
            base_url="http://remote-node-a.example.com",
            api_base_url="http://remote-node-a.example.com/api",
            username="remote_user",
            password="remote_pass",
            is_active=True,
        )
        self.inbox_url = f"/api/authors/{self.owner.serial}/inbox"

    def test_inbox_requires_auth(self):
        payload = {"type": "entry", "id": "http://remote-node-a.example.com/api/authors/r1/entries/e1"}
        resp = self.client.post(self.inbox_url, payload, format="json")
        self.assertEqual(resp.status_code, 401)

    def test_remote_entry_post_creates_entry_and_event(self):
        payload = {
            "type": "entry",
            "id": "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111/entries/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "title": "Remote entry",
            "content": "hello from remote",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "author": {
                "type": "author",
                "id": "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111",
                "host": "http://remote-node-a.example.com/api/",
                "displayName": "Remote User",
                "github": "https://github.com/remote-user",
                "profileImage": "https://placehold.co/64x64.png",
                "web": "http://remote-node-a.example.com/authors/11111111-1111-1111-1111-111111111111",
            },
        }
        resp = self.client.post(
            self.inbox_url,
            payload,
            format="json",
            HTTP_AUTHORIZATION=basic_auth_value("remote_user", "remote_pass"),
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(InboxItem.objects.count(), 1)

    def test_reposting_same_event_is_idempotent(self):
        payload = {
            "type": "entry",
            "id": "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111/entries/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "title": "Duplicate entry event",
            "content": "duplicate",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "author": {
                "type": "author",
                "id": "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111",
                "host": "http://remote-node-a.example.com/api/",
                "displayName": "Remote User",
                "github": "https://github.com/remote-user",
                "profileImage": "https://placehold.co/64x64.png",
                "web": "http://remote-node-a.example.com/authors/11111111-1111-1111-1111-111111111111",
            },
        }
        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}
        first = self.client.post(self.inbox_url, payload, format="json", **headers)
        second = self.client.post(self.inbox_url, payload, format="json", **headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(InboxItem.objects.count(), 1)

    def test_entry_update_same_fqid_processes_as_new_event(self):
        entry_id = "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111/entries/cccccccc-cccc-cccc-cccc-cccccccccccc"
        author_payload = {
            "type": "author",
            "id": "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111",
            "host": "http://remote-node-a.example.com/api/",
            "displayName": "Remote User",
            "github": "https://github.com/remote-user",
            "profileImage": "https://placehold.co/64x64.png",
            "web": "http://remote-node-a.example.com/authors/11111111-1111-1111-1111-111111111111",
        }
        first_payload = {
            "type": "entry",
            "id": entry_id,
            "title": "Original title",
            "content": "original body",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "published": "2026-03-26T01:00:00Z",
            "author": author_payload,
        }
        second_payload = {
            **first_payload,
            "title": "Updated title",
            "content": "updated body",
            "published": "2026-03-26T02:00:00Z",
        }

        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}
        first = self.client.post(self.inbox_url, first_payload, format="json", **headers)
        second = self.client.post(self.inbox_url, second_payload, format="json", **headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(Entry.objects.count(), 1)
        entry = Entry.objects.get(url=entry_id)
        self.assertEqual(entry.title, "Updated title")
        self.assertEqual(entry.content, "updated body")
        self.assertEqual(entry.published, parse_datetime("2026-03-26T02:00:00Z"))
        self.assertEqual(InboxItem.objects.filter(owner=self.owner).count(), 2)

    def test_entry_delete_same_fqid_processes_after_create(self):
        entry_id = "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111/entries/dddddddd-dddd-dddd-dddd-dddddddddddd"
        author_payload = {
            "type": "author",
            "id": "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111",
            "host": "http://remote-node-a.example.com/api/",
            "displayName": "Remote User",
            "github": "https://github.com/remote-user",
            "profileImage": "https://placehold.co/64x64.png",
            "web": "http://remote-node-a.example.com/authors/11111111-1111-1111-1111-111111111111",
        }
        create_payload = {
            "type": "entry",
            "id": entry_id,
            "title": "Delete me",
            "content": "body",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "published": "2026-03-26T03:00:00Z",
            "author": author_payload,
        }
        delete_payload = {
            **create_payload,
            "visibility": "DELETED",
            "published": "2026-03-26T04:00:00Z",
        }

        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}
        first = self.client.post(self.inbox_url, create_payload, format="json", **headers)
        second = self.client.post(self.inbox_url, delete_payload, format="json", **headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        entry = Entry.objects.get(url=entry_id)
        self.assertEqual(entry.visibility, "DELETED")
        self.assertEqual(entry.published, parse_datetime("2026-03-26T04:00:00Z"))
        self.assertEqual(InboxItem.objects.filter(owner=self.owner).count(), 2)

    def test_remote_published_timestamps_are_preserved_for_entry_comment_and_like(self):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/timestamp-user",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Timestamp User",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/timestamp-user",
        )
        local_entry = Entry.objects.create(
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}",
            author=self.owner,
            title="Local entry",
            content="local body",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}

        entry_published = "2026-03-26T05:00:00Z"
        entry_payload = {
            "type": "entry",
            "id": "http://remote-node-a.example.com/api/authors/timestamp-user/entries/eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            "title": "Timestamped entry",
            "content": "remote body",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "published": entry_published,
            "author": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
        }
        entry_resp = self.client.post(self.inbox_url, entry_payload, format="json", **headers)
        self.assertEqual(entry_resp.status_code, 201)
        remote_entry = Entry.objects.get(url=entry_payload["id"])
        self.assertEqual(remote_entry.published, parse_datetime(entry_published))

        comment_published = "2026-03-26T06:00:00Z"
        comment_payload = {
            "type": "comment",
            "id": "http://remote-node-a.example.com/api/authors/timestamp-user/commented/ffffffff-ffff-ffff-ffff-ffffffffffff",
            "entry": local_entry.url,
            "contentType": "text/plain",
            "comment": "dated comment",
            "published": comment_published,
            "author": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
        }
        comment_resp = self.client.post(self.inbox_url, comment_payload, format="json", **headers)
        self.assertEqual(comment_resp.status_code, 201)
        comment = Comment.objects.get(url=comment_payload["id"])
        self.assertEqual(comment.published, parse_datetime(comment_published))

        like_published = "2026-03-26T07:00:00Z"
        like_payload = {
            "type": "like",
            "id": "http://remote-node-a.example.com/api/authors/timestamp-user/liked/timestamp-like",
            "object": local_entry.url,
            "published": like_published,
            "author": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
        }
        like_resp = self.client.post(self.inbox_url, like_payload, format="json", **headers)
        self.assertEqual(like_resp.status_code, 201)
        like = EntryLike.objects.get(author=remote_author, entry=local_entry)
        self.assertEqual(like.published, parse_datetime(like_published))

    def test_remote_entry_preserves_incoming_web_url(self):
        payload = {
            "type": "entry",
            "id": "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111/entries/web-preserved",
            "title": "Remote entry",
            "content": "hello from remote",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
            "web": "http://remote-node-a.example.com/authors/11111111-1111-1111-1111-111111111111/posts/web-preserved",
            "author": {
                "type": "author",
                "id": "http://remote-node-a.example.com/api/authors/11111111-1111-1111-1111-111111111111",
                "host": "http://remote-node-a.example.com/api/",
                "displayName": "Remote User",
                "github": "https://github.com/remote-user",
                "profileImage": "https://placehold.co/64x64.png",
                "web": "http://remote-node-a.example.com/authors/11111111-1111-1111-1111-111111111111",
            },
        }

        resp = self.client.post(
            self.inbox_url,
            payload,
            format="json",
            HTTP_AUTHORIZATION=basic_auth_value("remote_user", "remote_pass"),
        )

        self.assertEqual(resp.status_code, 201)
        entry = Entry.objects.get(url=payload["id"])
        self.assertEqual(entry.web, payload["web"])
        self.assertEqual(resp.data["web"], payload["web"])

    def test_follow_comment_like_payloads_create_objects(self):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/22222222-2222-2222-2222-222222222222",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Actor",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/22222222-2222-2222-2222-222222222222",
        )
        entry = Entry.objects.create(
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}",
            author=self.owner,
            title="Local entry",
            content="local",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        comment = Comment.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a/api/authors/22222222-2222-2222-2222-222222222222/commented/33333333-3333-3333-3333-333333333333",
            author=remote_author,
            entry=entry,
            content_type="text/plain",
            content="existing comment",
        )

        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}
        follow_payload = {
            "type": "follow",
            "id": "http://remote-node-a.example.com/api/follows/f1",
            "actor": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
            "object": {
                "id": self.owner.url,
                "host": self.owner.host,
                "displayName": self.owner.displayName,
                "github": "",
                "profileImage": self.owner.profileImage,
                "web": self.owner.web,
            },
        }
        follow_resp = self.client.post(self.inbox_url, follow_payload, format="json", **headers)
        self.assertEqual(follow_resp.status_code, 201)
        self.assertTrue(Follow.objects.filter(actor=remote_author, target=self.owner).exists())

        comment_payload = {
            "type": "comment",
            "id": "http://remote-node-a.example.com/api/authors/22222222-2222-2222-2222-222222222222/commented/44444444-4444-4444-4444-444444444444",
            "entry": entry.url,
            "contentType": "text/plain",
            "comment": "new inbox comment",
            "author": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
        }
        comment_resp = self.client.post(self.inbox_url, comment_payload, format="json", **headers)
        self.assertEqual(comment_resp.status_code, 201)
        self.assertTrue(Comment.objects.filter(url=comment_payload["id"]).exists())

        like_payload = {
            "type": "like",
            "id": "http://remote-node-a.example.com/api/authors/22222222-2222-2222-2222-222222222222/liked/l1",
            "object": comment.url,
            "author": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
        }
        like_resp = self.client.post(self.inbox_url, like_payload, format="json", **headers)
        self.assertEqual(like_resp.status_code, 201)
        self.assertTrue(CommentLike.objects.filter(author=remote_author, comment=comment).exists())

        unlike_payload = {
            "type": "unlike",
            "id": "http://remote-node-a.example.com/api/authors/22222222-2222-2222-2222-222222222222/unlikes/u1",
            "object": comment.url,
            "author": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
        }
        unlike_resp = self.client.post(self.inbox_url, unlike_payload, format="json", **headers)
        self.assertEqual(unlike_resp.status_code, 201)
        self.assertFalse(CommentLike.objects.filter(author=remote_author, comment=comment).exists())

    def test_like_payload_resolves_entry_when_object_host_differs(self):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Liker",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        entry = Entry.objects.create(
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}",
            author=self.owner,
            title="Local entry",
            content="local",
            content_type="text/plain",
            visibility="PUBLIC",
        )

        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}
        equivalent_remote_object = (
            f"http://remote-node-a.example.com/api/authors/{self.owner.serial}/entries/{entry.serial}"
        )
        like_payload = {
            "type": "like",
            "id": "http://remote-node-a.example.com/api/authors/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/liked/l-host-variant",
            "object": equivalent_remote_object,
            "author": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
        }

        like_resp = self.client.post(self.inbox_url, like_payload, format="json", **headers)

        self.assertEqual(like_resp.status_code, 201)
        self.assertTrue(EntryLike.objects.filter(author=remote_author, entry=entry).exists())

    def test_duplicate_follow_does_not_downgrade_accepted_follow(self):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-follow-accepted",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Accepted",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/remote-follow-accepted",
        )
        Follow.objects.create(actor=remote_author, target=self.owner, status="ACCEPTED")
        payload = {
            "type": "follow",
            "id": "http://remote-node-a.example.com/api/follows/f-accepted",
            "actor": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
            "object": {
                "id": self.owner.url,
                "host": self.owner.host,
                "displayName": self.owner.displayName,
                "github": "",
                "profileImage": self.owner.profileImage,
                "web": self.owner.web,
            },
        }

        resp = self.client.post(
            self.inbox_url,
            payload,
            format="json",
            HTTP_AUTHORIZATION=basic_auth_value("remote_user", "remote_pass"),
        )

        self.assertEqual(resp.status_code, 201)
        follow = Follow.objects.get(actor=remote_author, target=self.owner)
        self.assertEqual(follow.status, "ACCEPTED")

    def test_follow_inbox_repost_same_event_is_idempotent(self):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-follow-idempotent",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Idempotent Follow",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/remote-follow-idempotent",
        )
        payload = {
            "type": "follow",
            "id": "http://remote-node-a.example.com/api/follows/f-idempotent",
            "actor": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
            "object": {
                "id": self.owner.url,
                "host": self.owner.host,
                "displayName": self.owner.displayName,
                "github": "",
                "profileImage": self.owner.profileImage,
                "web": self.owner.web,
            },
        }
        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}

        first = self.client.post(self.inbox_url, payload, format="json", **headers)
        second = self.client.post(self.inbox_url, payload, format="json", **headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            Follow.objects.filter(actor=remote_author, target=self.owner).count(),
            1,
        )
        self.assertEqual(InboxItem.objects.filter(owner=self.owner, item_id=payload["id"]).count(), 1)

    def test_accept_inbox_marks_follow_as_accepted(self):
        remote_followee = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-followee",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Followee",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/remote-followee",
        )
        Follow.objects.create(actor=self.owner, target=remote_followee, status="REQUESTED")
        payload = {
            "type": "accept",
            "id": "http://remote-node-a.example.com/api/accepts/a1",
            "actor": {
                "id": remote_followee.url,
                "host": remote_followee.host,
                "displayName": remote_followee.displayName,
                "github": "",
                "profileImage": remote_followee.profileImage,
                "web": remote_followee.web,
            },
            "object": {
                "id": self.owner.url,
                "host": self.owner.host,
                "displayName": self.owner.displayName,
                "github": "",
                "profileImage": self.owner.profileImage,
                "web": self.owner.web,
            },
        }

        resp = self.client.post(
            self.inbox_url,
            payload,
            format="json",
            HTTP_AUTHORIZATION=basic_auth_value("remote_user", "remote_pass"),
        )

        self.assertEqual(resp.status_code, 201)
        follow = Follow.objects.get(actor=self.owner, target=remote_followee)
        self.assertEqual(follow.status, "ACCEPTED")

    def test_accept_inbox_repost_same_event_is_idempotent(self):
        remote_followee = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-followee-idempotent",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Followee Idempotent",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/remote-followee-idempotent",
        )
        Follow.objects.create(actor=self.owner, target=remote_followee, status="REQUESTED")
        payload = {
            "type": "accept",
            "id": "http://remote-node-a.example.com/api/accepts/a-idempotent",
            "actor": {
                "id": remote_followee.url,
                "host": remote_followee.host,
                "displayName": remote_followee.displayName,
                "github": "",
                "profileImage": remote_followee.profileImage,
                "web": remote_followee.web,
            },
            "object": {
                "id": self.owner.url,
                "host": self.owner.host,
                "displayName": self.owner.displayName,
                "github": "",
                "profileImage": self.owner.profileImage,
                "web": self.owner.web,
            },
        }
        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}

        first = self.client.post(self.inbox_url, payload, format="json", **headers)
        second = self.client.post(self.inbox_url, payload, format="json", **headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            Follow.objects.filter(actor=self.owner, target=remote_followee, status="ACCEPTED").count(),
            1,
        )
        self.assertEqual(InboxItem.objects.filter(owner=self.owner, item_id=payload["id"]).count(), 1)

    def test_unfollow_inbox_removes_follow_row(self):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-unfollow",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Unfollow",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/remote-unfollow",
        )
        Follow.objects.create(actor=remote_author, target=self.owner, status="REQUESTED")
        payload = {
            "type": "unfollow",
            "id": "http://remote-node-a.example.com/api/unfollows/u1",
            "actor": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
            "object": {
                "id": self.owner.url,
                "host": self.owner.host,
                "displayName": self.owner.displayName,
                "github": "",
                "profileImage": self.owner.profileImage,
                "web": self.owner.web,
            },
        }

        resp = self.client.post(
            self.inbox_url,
            payload,
            format="json",
            HTTP_AUTHORIZATION=basic_auth_value("remote_user", "remote_pass"),
        )

        self.assertEqual(resp.status_code, 201)
        self.assertFalse(Follow.objects.filter(actor=remote_author, target=self.owner).exists())

    def test_unfollow_inbox_repost_same_event_is_idempotent(self):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-unfollow-idempotent",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote Unfollow Idempotent",
            github="",
            profileImage="https://placehold.co/60x60.png",
            web="http://remote-node-a.example.com/authors/remote-unfollow-idempotent",
        )
        Follow.objects.create(actor=remote_author, target=self.owner, status="REQUESTED")
        payload = {
            "type": "unfollow",
            "id": "http://remote-node-a.example.com/api/unfollows/u-idempotent",
            "actor": {
                "id": remote_author.url,
                "host": remote_author.host,
                "displayName": remote_author.displayName,
                "github": "",
                "profileImage": remote_author.profileImage,
                "web": remote_author.web,
            },
            "object": {
                "id": self.owner.url,
                "host": self.owner.host,
                "displayName": self.owner.displayName,
                "github": "",
                "profileImage": self.owner.profileImage,
                "web": self.owner.web,
            },
        }
        headers = {"HTTP_AUTHORIZATION": basic_auth_value("remote_user", "remote_pass")}

        first = self.client.post(self.inbox_url, payload, format="json", **headers)
        second = self.client.post(self.inbox_url, payload, format="json", **headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(Follow.objects.filter(actor=remote_author, target=self.owner).exists())
        self.assertEqual(InboxItem.objects.filter(owner=self.owner, item_id=payload["id"]).count(), 1)
