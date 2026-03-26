import base64
import uuid

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from core.models import Author, Comment, CommentLike, Entry, Follow, InboxItem, RemoteNode


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
