from rest_framework.test import APITestCase
from django.contrib.auth.models import User
import requests
from core.models import Author, Follow, RemoteNode
from core.helpers import build_remote_author_inbox_url, resolve_remote_author
import uuid
import base64
import urllib
from unittest.mock import patch, Mock


class FollowAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.author1 = Author.objects.create(user=self.user1, displayName="user1", serial=uuid.uuid4(), url=f"http://testserver/api/authors/{uuid.uuid4()}")

        self.user2 = User.objects.create_user(username="user2", password="password2")
        self.author2 = Author.objects.create(user=self.user2, displayName="user2", serial=uuid.uuid4(), url=f"http://testserver/api/authors/{uuid.uuid4()}")

        self.user3 = User.objects.create_user(username="user3", password="password3")
        self.author3 = Author.objects.create(user=self.user3, displayName="user3", serial=uuid.uuid4(), url=f"http://testserver/api/authors/{uuid.uuid4()}")

        self.user4 = User.objects.create_user(username="user4", password="password4")
        self.author4 = Author.objects.create(user=self.user4, displayName="user4", serial=uuid.uuid4(), url=f"http://testserver/api/authors/{uuid.uuid4()}")
    
        Follow.objects.create(actor=self.author2, target=self.author1, status="REQUESTED")
        Follow.objects.create(actor=self.author1, target=self.author3, status="ACCEPTED")
        self.remote_node = RemoteNode.objects.create(
            name="remote-auth-node",
            base_url="http://remote-auth-node.example.com",
            api_base_url="http://remote-auth-node.example.com/api",
            username="remote_user",
            password="remote_pass",
            is_active=True,
        )
        Follow.objects.create(actor=self.author1, target=self.author4, status="REQUESTED")

        self.encoded_a1_fqid = urllib.parse.quote(self.author1.url, safe='')
        self.encoded_a2_fqid = urllib.parse.quote(self.author2.url, safe='')
        self.encoded_a3_fqid = urllib.parse.quote(self.author3.url, safe='')
        self.encoded_a4_fqid = urllib.parse.quote(self.author4.url, safe='')

    def testFollowingList(self):
        """Authenticated author sees only accepted follows in following list."""
        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/following")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'following')

        following = [author['displayName'] for author in response.data['following']]

        self.assertIn(self.author3.displayName, following)
        self.assertNotIn(self.author2.displayName, following)
    
    def testFollowRequests(self):
        """Authenticated author sees only pending follow requests in requests list."""
        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/follow_requests")

        self.assertEqual(response.status_code, 200)

        followRequests = [item['actor']['displayName'] for item in response.data]

        self.assertIn(self.author2.displayName, followRequests)
        self.assertNotIn(self.author3.displayName, followRequests)

    def test_follower_check_allows_remote_basic_auth(self):
        """Remote node basic auth can call follower check endpoint."""
        follow = Follow.objects.get(actor=self.author2, target=self.author1)
        follow.status = "ACCEPTED"
        follow.save(update_fields=["status"])
        fqid = self.author2.url
        encoded = base64.b64encode(b"remote_user:remote_pass").decode("utf-8")
        response = self.client.get(
            f"/api/authors/{self.author1.serial}/followers/{fqid}",
            HTTP_AUTHORIZATION=f"Basic {encoded}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("type"), "author")
        self.assertEqual(response.data.get("id"), str(self.author2.url))

    def test_following_get_when_following(self):
        """GET should return true if the follow status is ACCEPTED."""
        self.client.login(username="user1", password="password1")
        self.client.put(f"/api/authors/{self.author1.serial}/following/{self.encoded_a3_fqid}")

        self.client.login(username="user1", password="password1")
        url = f"/api/authors/{self.author1.serial}/following/{self.encoded_a3_fqid}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_following'])

    def test_following_get_when_not_following(self):
        """GET should return false if the follow status is only REQUESTED, or doesn't exist."""
        self.client.login(username="user1", password="password1")
        self.client.put(f"/api/authors/{self.author1.serial}/following/{self.encoded_a4_fqid}")

        # Follow relationship is requested but not accepted
        url_requested = f"/api/authors/{self.author1.serial}/following/{self.encoded_a4_fqid}"
        response1 = self.client.get(url_requested)
        self.assertEqual(response1.status_code, 200)
        self.assertFalse(response1.data['is_following'])

        # Follow relationship does not exist at all
        url_empty = f"/api/authors/{self.author1.serial}/following/{self.encoded_a2_fqid}"
        response2 = self.client.get(url_empty)
        self.assertEqual(response2.status_code, 200)
        self.assertFalse(response2.data['is_following'])

    def test_following_put_creates_request(self):
        """PUT should create a REQUESTED follow relationship."""
        # User 1 sends the PUT request
        self.client.login(username="user1", password="password1")
        url = f"/api/authors/{self.author1.serial}/following/{self.encoded_a2_fqid}"
        response = self.client.put(url)
        self.assertEqual(response.status_code, 204)
        
        # Verify via API by having User 2 check their requests
        self.client.login(username="user2", password="password2")
        requests_response = self.client.get(f"/api/authors/{self.author2.serial}/follow_requests")
        requesters = [item['actor']['displayName'] for item in requests_response.data]
        self.assertIn(self.author1.displayName, requesters)

    def test_following_delete_relationship(self):
        """DELETE should completely remove the follow relationship."""
        # Setup: Create an accepted relationship
        self.client.login(username="user1", password="password1")
        self.client.put(f"/api/authors/{self.author1.serial}/following/{self.encoded_a2_fqid}")
        self.client.login(username="user2", password="password2")
        self.client.put(f"/api/authors/{self.author2.serial}/followers/{self.encoded_a1_fqid}")
        
        # User 1 deletes it
        self.client.login(username="user1", password="password1")
        url = f"/api/authors/{self.author1.serial}/following/{self.encoded_a2_fqid}"
        delete_response = self.client.delete(url)
        self.assertEqual(delete_response.status_code, 204)
        
        # Verify via API that GET now returns false
        get_response = self.client.get(url)
        self.assertFalse(get_response.data['is_following'])

    def test_following_unauthorized_access(self):
        """A user should get a 403 if they try to manage someone else's following list."""
        self.client.login(username="user3", password="password3") # Logged in as User 3!
        
        # Trying to edit User 1's list
        url = f"/api/authors/{self.author1.serial}/following/{self.encoded_a2_fqid}"
        response = self.client.put(url)
        
        self.assertEqual(response.status_code, 403)

    @patch("core.helpers.requests.get")
    def test_resolve_remote_author_fetches_uncached_author_profile(self, mock_get):
        fqid = "http://remote-auth-node.example.com/api/authors/remote-user"
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            "type": "author",
            "id": fqid,
            "host": "http://remote-auth-node.example.com/api/",
            "displayName": "Remote User",
            "github": "http://github.com/remote-user",
            "profileImage": "http://remote-auth-node.example.com/media/remote-user.png",
            "web": "http://remote-auth-node.example.com/authors/remote-user",
        }
        mock_get.return_value = mock_response

        author = resolve_remote_author(fqid)

        self.assertIsNotNone(author)
        self.assertEqual(author.url, fqid)
        self.assertEqual(author.host, "http://remote-auth-node.example.com/api")
        self.assertEqual(author.displayName, "Remote User")
        self.assertEqual(author.github, "http://github.com/remote-user")

    @patch("core.helpers.requests.get")
    def test_resolve_remote_author_falls_back_to_stub_on_fetch_failure(self, mock_get):
        fqid = "http://remote-auth-node.example.com/api/authors/stub-user"
        mock_get.side_effect = requests.exceptions.ConnectionError("unreachable")

        author = resolve_remote_author(fqid)

        self.assertIsNotNone(author)
        self.assertEqual(author.url, fqid)
        self.assertEqual(author.host, "http://remote-auth-node.example.com/api")
        self.assertEqual(author.displayName, "stub-user")
        self.assertEqual(author.web, "http://remote-auth-node.example.com/authors/stub-user")

    def test_resolve_remote_author_matches_trailing_slash_variant(self):
        existing = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-auth-node.example.com/api/authors/existing-user/",
            host="http://remote-auth-node.example.com/api/",
            displayName="Existing User",
        )

        resolved = resolve_remote_author("http://remote-auth-node.example.com/api/authors/existing-user")

        self.assertEqual(resolved.pk, existing.pk)

    def test_build_remote_author_inbox_url_from_fqid(self):
        inbox_url = build_remote_author_inbox_url(
            "http://remote-auth-node.example.com/api/authors/remote-user"
        )

        self.assertEqual(
            inbox_url,
            "http://remote-auth-node.example.com/api/authors/remote-user/inbox",
        )

    def test_follower_get_when_is_follower(self):
        """GET should return the follower author object when status is ACCEPTED."""
        # User 2 follows User 1, User 1 accepts
        self.client.login(username="user2", password="password2")
        self.client.put(f"/api/authors/{self.author2.serial}/following/{self.encoded_a1_fqid}")
        self.client.login(username="user1", password="password1")
        self.client.put(f"/api/authors/{self.author1.serial}/followers/{self.encoded_a2_fqid}")
        
        # User 1 checks if User 2 is a follower
        url = f"/api/authors/{self.author1.serial}/followers/{self.encoded_a2_fqid}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("type"), "author")
        self.assertEqual(response.data.get("id"), self.author2.url)

    def test_follower_get_when_not_follower(self):
        """GET should return 404 when the foreign author is not an accepted follower."""
        # User 2 requests to follow User 1 (not accepted)
        self.client.login(username="user2", password="password2")
        self.client.put(f"/api/authors/{self.author2.serial}/following/{self.encoded_a1_fqid}")
        
        self.client.login(username="user1", password="password1")
        url = f"/api/authors/{self.author1.serial}/followers/{self.encoded_a2_fqid}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

    def test_follower_put_accepts_request(self):
        """PUT should change a REQUESTED relationship into an ACCEPTED one."""
        # User 2 requests to follow User 1
        self.client.login(username="user2", password="password2")
        self.client.put(f"/api/authors/{self.author2.serial}/following/{self.encoded_a1_fqid}")
        
        # User 1 accepts the request
        self.client.login(username="user1", password="password1")
        url = f"/api/authors/{self.author1.serial}/followers/{self.encoded_a2_fqid}"
        put_response = self.client.put(url)
        self.assertEqual(put_response.status_code, 204)
        
        # Verify via API that User 2 is now a confirmed follower object
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data.get("id"), self.author2.url)

    def test_follower_delete_removes_follower(self):
        """DELETE should completely remove the follower."""
        # User 2 follows User 1, User 1 accepts
        self.client.login(username="user2", password="password2")
        self.client.put(f"/api/authors/{self.author2.serial}/following/{self.encoded_a1_fqid}")
        self.client.login(username="user1", password="password1")
        self.client.put(f"/api/authors/{self.author1.serial}/followers/{self.encoded_a2_fqid}")
        
        # User 1 forces User 2 to unfollow them
        url = f"/api/authors/{self.author1.serial}/followers/{self.encoded_a2_fqid}"
        delete_response = self.client.delete(url)
        self.assertEqual(delete_response.status_code, 204)
        
        # Verify via API that User 2 is no longer a follower
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 404)

    def test_follower_unauthorized_access(self):
        """A user should get a 403 if they try to manage someone else's followers."""
        self.client.login(username="user3", password="password3") # Logged in as User 3!
        
        # Trying to accept a follower for user 1 as user 3
        url = f"/api/authors/{self.author1.serial}/followers/{self.encoded_a2_fqid}"
        response = self.client.put(url)
        
        self.assertEqual(response.status_code, 403)

    @patch("core.apis.follow_api.notify_remote_follow_acceptance")
    def test_follower_put_calls_remote_acceptance_callback_for_remote_follower(self, mock_notify):
        mock_notify.return_value = (True, None)
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://127.0.0.1:8001/api/authors/remote-follower",
            host="http://127.0.0.1:8001/api/",
            displayName="Remote Follower",
        )
        Follow.objects.create(actor=remote_author, target=self.author1, status="REQUESTED")
        encoded_remote = urllib.parse.quote(remote_author.url, safe="")

        self.client.login(username="user1", password="password1")
        response = self.client.put(f"/api/authors/{self.author1.serial}/followers/{encoded_remote}")

        self.assertEqual(response.status_code, 204)
        mock_notify.assert_called_once_with(remote_author, self.author1)

    @patch("core.apis.follow_api.notify_remote_follow_acceptance")
    def test_follower_put_returns_502_when_remote_acceptance_callback_fails(self, mock_notify):
        mock_notify.return_value = (False, "remote callback failed")
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://127.0.0.1:8001/api/authors/remote-follower-2",
            host="http://127.0.0.1:8001/api/",
            displayName="Remote Follower 2",
        )
        Follow.objects.create(actor=remote_author, target=self.author1, status="REQUESTED")
        encoded_remote = urllib.parse.quote(remote_author.url, safe="")

        self.client.login(username="user1", password="password1")
        response = self.client.put(f"/api/authors/{self.author1.serial}/followers/{encoded_remote}")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data.get("error"), "remote callback failed")
    
