from rest_framework.test import APITestCase
from django.contrib.auth.models import User
import requests
from core.apis.follow_api import (
    forward_follow_request_to_remote_inbox,
    notify_remote_follow_acceptance,
)
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
        """Authenticated author sees requested and accepted follows in following list."""
        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/following")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'following')

        following = [author['displayName'] for author in response.data['following']]

        self.assertIn(self.author3.displayName, following)
        self.assertIn(self.author4.displayName, following)
        self.assertNotIn(self.author2.displayName, following)
    
    def testFollowRequests(self):
        """Authenticated author sees only pending follow requests in requests list."""
        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/follow_requests")

        self.assertEqual(response.status_code, 200)

        followRequests = [item['actor']['displayName'] for item in response.data]

        self.assertIn(self.author2.displayName, followRequests)
        self.assertNotIn(self.author3.displayName, followRequests)

    def test_following_collection_is_sorted_by_display_name(self):
        alpha_user = User.objects.create_user(username="alpha-user", password="password5")
        alpha_author = Author.objects.create(
            user=alpha_user,
            displayName="alpha",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        zeta_user = User.objects.create_user(username="zeta-user", password="password6")
        zeta_author = Author.objects.create(
            user=zeta_user,
            displayName="zeta",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        Follow.objects.create(actor=self.author1, target=zeta_author, status="REQUESTED")
        Follow.objects.create(actor=self.author1, target=alpha_author, status="ACCEPTED")

        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/following")

        names = [author["displayName"] for author in response.data["following"]]
        self.assertEqual(names, sorted(names))

    def test_following_collection_supports_page_and_size(self):
        alpha_user = User.objects.create_user(username="alpha-page-user", password="password5")
        alpha_author = Author.objects.create(
            user=alpha_user,
            displayName="alpha page",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        beta_user = User.objects.create_user(username="beta-page-user", password="password6")
        beta_author = Author.objects.create(
            user=beta_user,
            displayName="beta page",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        Follow.objects.create(actor=self.author1, target=alpha_author, status="REQUESTED")
        Follow.objects.create(actor=self.author1, target=beta_author, status="ACCEPTED")

        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/following?page=1&size=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["page_number"], 1)
        self.assertEqual(response.data["size"], 2)
        self.assertGreaterEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["following"]), 2)

    def test_follow_requests_are_sorted_by_actor_display_name(self):
        alpha_user = User.objects.create_user(username="alpha-requester", password="password5")
        alpha_author = Author.objects.create(
            user=alpha_user,
            displayName="alpha requester",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        zeta_user = User.objects.create_user(username="zeta-requester", password="password6")
        zeta_author = Author.objects.create(
            user=zeta_user,
            displayName="zeta requester",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        Follow.objects.create(actor=zeta_author, target=self.author1, status="REQUESTED")
        Follow.objects.create(actor=alpha_author, target=self.author1, status="REQUESTED")

        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/follow_requests")

        names = [item["actor"]["displayName"] for item in response.data]
        self.assertEqual(names, sorted(names))

    def test_follow_requests_supports_page_and_size_with_same_response_shape(self):
        alpha_user = User.objects.create_user(username="alpha-paged-requester", password="password5")
        alpha_author = Author.objects.create(
            user=alpha_user,
            displayName="alpha paged requester",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        beta_user = User.objects.create_user(username="beta-paged-requester", password="password6")
        beta_author = Author.objects.create(
            user=beta_user,
            displayName="beta paged requester",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        Follow.objects.create(actor=alpha_author, target=self.author1, status="REQUESTED")
        Follow.objects.create(actor=beta_author, target=self.author1, status="REQUESTED")

        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/follow_requests?page=1&size=1")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

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

    def test_followers_collection_returns_only_accepted_followers_for_remote_basic_auth(self):
        accepted_follow = Follow.objects.get(actor=self.author2, target=self.author1)
        accepted_follow.status = "ACCEPTED"
        accepted_follow.save(update_fields=["status"])
        encoded = base64.b64encode(b"remote_user:remote_pass").decode("utf-8")

        response = self.client.get(
            f"/api/authors/{self.author1.serial}/followers",
            HTTP_AUTHORIZATION=f"Basic {encoded}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "followers")
        followers = [author["id"] for author in response.data["followers"]]
        self.assertIn(self.author2.url, followers)
        self.assertNotIn(self.author3.url, followers)

    def test_followers_collection_is_sorted_by_display_name(self):
        alpha_user = User.objects.create_user(username="alpha-follower", password="password5")
        alpha_author = Author.objects.create(
            user=alpha_user,
            displayName="alpha follower",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        zeta_user = User.objects.create_user(username="zeta-follower", password="password6")
        zeta_author = Author.objects.create(
            user=zeta_user,
            displayName="zeta follower",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        Follow.objects.create(actor=zeta_author, target=self.author1, status="ACCEPTED")
        Follow.objects.create(actor=alpha_author, target=self.author1, status="ACCEPTED")

        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/followers")

        names = [author["displayName"] for author in response.data["followers"]]
        self.assertEqual(names, sorted(names))

    def test_followers_collection_supports_page_and_size_for_remote_auth(self):
        alpha_user = User.objects.create_user(username="alpha-page-follower", password="password5")
        alpha_author = Author.objects.create(
            user=alpha_user,
            displayName="alpha page follower",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        beta_user = User.objects.create_user(username="beta-page-follower", password="password6")
        beta_author = Author.objects.create(
            user=beta_user,
            displayName="beta page follower",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        Follow.objects.create(actor=alpha_author, target=self.author1, status="ACCEPTED")
        Follow.objects.create(actor=beta_author, target=self.author1, status="ACCEPTED")
        encoded = base64.b64encode(b"remote_user:remote_pass").decode("utf-8")

        response = self.client.get(
            f"/api/authors/{self.author1.serial}/followers?page=1&size=1",
            HTTP_AUTHORIZATION=f"Basic {encoded}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["page_number"], 1)
        self.assertEqual(response.data["size"], 1)
        self.assertGreaterEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["followers"]), 1)

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
        """GET should return false only when no follow relationship exists."""
        self.client.login(username="user1", password="password1")
        self.client.put(f"/api/authors/{self.author1.serial}/following/{self.encoded_a4_fqid}")

        # Follow relationship is requested and still counts as following on the actor node
        url_requested = f"/api/authors/{self.author1.serial}/following/{self.encoded_a4_fqid}"
        response1 = self.client.get(url_requested)
        self.assertEqual(response1.status_code, 200)
        self.assertTrue(response1.data['is_following'])

        # Follow relationship does not exist at all
        url_empty = f"/api/authors/{self.author1.serial}/following/{self.encoded_a2_fqid}"
        response2 = self.client.get(url_empty)
        self.assertEqual(response2.status_code, 200)
        self.assertFalse(response2.data['is_following'])

    def test_following_get_matches_trailing_slash_fqid_variant(self):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-auth-node.example.com/api/authors/slash-user/",
            host="http://remote-auth-node.example.com/api/",
            displayName="Slash User",
        )
        Follow.objects.create(actor=self.author1, target=remote_author, status="REQUESTED")

        self.client.login(username="user1", password="password1")
        response = self.client.get(
            f"/api/authors/{self.author1.serial}/following/{urllib.parse.quote('http://remote-auth-node.example.com/api/authors/slash-user', safe='')}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_following"])

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

    @patch("core.apis.follow_api.forward_follow_request_to_remote_inbox")
    @patch("core.helpers.requests.get")
    def test_following_put_resolves_uncached_remote_author(self, mock_get, mock_forward):
        remote_fqid = "http://remote-auth-node.example.com/api/authors/new-remote-user"
        encoded_remote = urllib.parse.quote(remote_fqid, safe="")
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            "type": "author",
            "id": remote_fqid,
            "host": "http://remote-auth-node.example.com/api/",
            "displayName": "New Remote User",
            "web": "http://remote-auth-node.example.com/authors/new-remote-user",
        }
        mock_get.return_value = mock_response
        mock_forward.return_value = (True, None)

        self.client.login(username="user1", password="password1")
        response = self.client.put(f"/api/authors/{self.author1.serial}/following/{encoded_remote}")

        self.assertEqual(response.status_code, 204)
        remote_author = Author.objects.get(url=remote_fqid)
        self.assertEqual(remote_author.displayName, "New Remote User")
        self.assertTrue(
            Follow.objects.filter(actor=self.author1, target=remote_author, status="REQUESTED").exists()
        )
        mock_forward.assert_called_once_with(self.author1, remote_author)

    @patch("core.apis.follow_api.forward_follow_request_to_remote_inbox")
    def test_following_put_remote_failure_does_not_leave_pending_row(self, mock_forward):
        mock_forward.return_value = (False, "remote inbox rejected")
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://127.0.0.1:8001/api/authors/remote-failure",
            host="http://127.0.0.1:8001/api/",
            displayName="Remote Failure",
        )
        encoded_remote = urllib.parse.quote(remote_author.url, safe="")

        self.client.login(username="user1", password="password1")
        response = self.client.put(f"/api/authors/{self.author1.serial}/following/{encoded_remote}")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data.get("error"), "remote inbox rejected")
        self.assertFalse(
            Follow.objects.filter(actor=self.author1, target=remote_author).exists()
        )

    @patch("core.apis.follow_api.send_json_to_remote_author_inbox")
    def test_forward_follow_request_contextualizes_rejection_errors(self, mock_send):
        mock_send.return_value = (False, "Remote inbox rejected request with status 401")
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://127.0.0.1:8001/api/authors/remote-follow-error",
            host="http://127.0.0.1:8001/api/",
            displayName="Remote Follow Error",
        )

        delivered, error = forward_follow_request_to_remote_inbox(self.author1, remote_author)

        self.assertFalse(delivered)
        self.assertEqual(error, "Remote inbox rejected follow request with status 401")

    def test_following_put_rejects_self_follow(self):
        self.client.login(username="user1", password="password1")
        response = self.client.put(
            f"/api/authors/{self.author1.serial}/following/{self.encoded_a1_fqid}"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data.get("error"),
            "Authors cannot follow themselves.",
        )

    def test_html_following_list_includes_requested_and_accepted(self):
        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/authors/{self.author1.serial}/following/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author3.displayName)
        self.assertContains(response, self.author4.displayName)

    def test_html_follow_requests_are_sorted_by_actor_display_name(self):
        alpha_user = User.objects.create_user(username="alpha-html-requester", password="password5")
        alpha_author = Author.objects.create(
            user=alpha_user,
            displayName="alpha html requester",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        zeta_user = User.objects.create_user(username="zeta-html-requester", password="password6")
        zeta_author = Author.objects.create(
            user=zeta_user,
            displayName="zeta html requester",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
        )
        Follow.objects.create(actor=zeta_author, target=self.author1, status="REQUESTED")
        Follow.objects.create(actor=alpha_author, target=self.author1, status="REQUESTED")

        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/authors/{self.author1.serial}/requests/")

        content = response.content.decode("utf-8")
        self.assertLess(
            content.index("alpha html requester"),
            content.index("zeta html requester"),
        )

    def test_html_follow_author_re_requests_rejected_follow(self):
        follow = Follow.objects.create(actor=self.author1, target=self.author2, status="REJECTED")

        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/authors/{self.author2.serial}/follow/")

        self.assertEqual(response.status_code, 302)
        follow.refresh_from_db()
        self.assertEqual(follow.status, "REQUESTED")

    @patch("core.views.follow_views.forward_follow_request_to_remote_inbox")
    def test_html_follow_author_failure_shows_error_and_preserves_state(self, mock_forward):
        mock_forward.return_value = (False, "remote inbox rejected")
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://127.0.0.1:8001/api/authors/remote-html-failure",
            host="http://127.0.0.1:8001/api/",
            displayName="Remote HTML Failure",
        )

        self.client.login(username="user1", password="password1")
        response = self.client.get(
            f"/authors/{remote_author.serial}/follow/",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "remote inbox rejected")
        self.assertFalse(
            Follow.objects.filter(actor=self.author1, target=remote_author).exists()
        )

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

    def test_follower_put_returns_404_without_pending_request(self):
        self.client.login(username="user1", password="password1")
        response = self.client.put(
            f"/api/authors/{self.author1.serial}/followers/{self.encoded_a3_fqid}"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.get("error"), "Follow request not found.")

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

    def test_follower_delete_returns_404_when_row_missing(self):
        self.client.login(username="user1", password="password1")
        response = self.client.delete(
            f"/api/authors/{self.author1.serial}/followers/{self.encoded_a3_fqid}"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.get("error"), "Follower not found")

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

    @patch("core.apis.follow_api.send_json_to_remote_author_inbox")
    def test_notify_remote_follow_acceptance_contextualizes_rejection_errors(self, mock_send):
        mock_send.return_value = (False, "Remote inbox rejected request with status 403")
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://127.0.0.1:8001/api/authors/remote-follower-error",
            host="http://127.0.0.1:8001/api/",
            displayName="Remote Follower Error",
        )

        delivered, error = notify_remote_follow_acceptance(remote_author, self.author1)

        self.assertFalse(delivered)
        self.assertEqual(error, "Remote inbox rejected accept with status 403")

    @patch("core.apis.follow_api.notify_remote_follow_acceptance")
    def test_follower_put_allows_remote_basic_auth_without_callback_loop(self, mock_notify):
        remote_author = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-auth-node.example.com/api/authors/remote-put-user",
            host="http://remote-auth-node.example.com/api/",
            displayName="Remote Put User",
        )
        encoded_remote = urllib.parse.quote(remote_author.url, safe="")
        encoded = base64.b64encode(b"remote_user:remote_pass").decode("utf-8")

        response1 = self.client.put(
            f"/api/authors/{self.author1.serial}/followers/{encoded_remote}",
            HTTP_AUTHORIZATION=f"Basic {encoded}",
        )
        response2 = self.client.put(
            f"/api/authors/{self.author1.serial}/followers/{encoded_remote}",
            HTTP_AUTHORIZATION=f"Basic {encoded}",
        )

        self.assertEqual(response1.status_code, 204)
        self.assertEqual(response2.status_code, 204)
        self.assertTrue(
            Follow.objects.filter(actor=remote_author, target=self.author1, status="ACCEPTED").exists()
        )
        self.assertEqual(
            Follow.objects.filter(actor=remote_author, target=self.author1).count(),
            1,
        )
        mock_notify.assert_not_called()

    @patch("core.apis.follow_api.send_json_to_remote_author_inbox")
    def test_forward_follow_request_skips_same_node_heroku_author(self, mock_send):
        actor_user = User.objects.create_user(username="same-node-actor", password="password5")
        actor = Author.objects.create(
            user=actor_user,
            serial=uuid.uuid4(),
            url="https://wheat-5111c2e081f4.herokuapp.com/api/authors/11111111-1111-1111-1111-111111111111",
            host="https://wheat-5111c2e081f4.herokuapp.com/api/",
            web="https://wheat-5111c2e081f4.herokuapp.com/authors/11111111-1111-1111-1111-111111111111/",
            displayName="Same Node Actor",
        )
        target_user = User.objects.create_user(username="same-node-target", password="password6")
        target = Author.objects.create(
            user=target_user,
            serial=uuid.uuid4(),
            url="https://wheat-5111c2e081f4.herokuapp.com/api/authors/22222222-2222-2222-2222-222222222222",
            host="https://wheat-5111c2e081f4.herokuapp.com/api/",
            web="https://wheat-5111c2e081f4.herokuapp.com/authors/22222222-2222-2222-2222-222222222222/",
            displayName="Same Node Target",
        )

        delivered, error = forward_follow_request_to_remote_inbox(actor, target)

        self.assertTrue(delivered)
        self.assertIsNone(error)
        mock_send.assert_not_called()

    def test_follow_view_creates_same_node_follow_on_heroku_without_remote_node_credentials(self):
        actor_user = User.objects.create_user(username="same-node-view-actor", password="password5")
        actor = Author.objects.create(
            user=actor_user,
            serial=uuid.uuid4(),
            url="https://wheat-5111c2e081f4.herokuapp.com/api/authors/33333333-3333-3333-3333-333333333333",
            host="https://wheat-5111c2e081f4.herokuapp.com/api/",
            web="https://wheat-5111c2e081f4.herokuapp.com/authors/33333333-3333-3333-3333-333333333333/",
            displayName="Same Node View Actor",
        )
        target_user = User.objects.create_user(username="same-node-view-target", password="password6")
        target = Author.objects.create(
            user=target_user,
            serial=uuid.uuid4(),
            url="https://wheat-5111c2e081f4.herokuapp.com/api/authors/44444444-4444-4444-4444-444444444444",
            host="https://wheat-5111c2e081f4.herokuapp.com/api/",
            web="https://wheat-5111c2e081f4.herokuapp.com/authors/44444444-4444-4444-4444-444444444444/",
            displayName="Same Node View Target",
        )

        self.client.login(username="same-node-view-actor", password="password5")
        response = self.client.get(f"/authors/{target.serial}/follow/")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Follow.objects.filter(actor=actor, target=target, status="REQUESTED").exists())

    def test_following_api_creates_same_node_follow_on_heroku_without_remote_node_credentials(self):
        actor_user = User.objects.create_user(username="same-node-api-actor", password="password5")
        actor = Author.objects.create(
            user=actor_user,
            serial=uuid.uuid4(),
            url="https://wheat-5111c2e081f4.herokuapp.com/api/authors/55555555-5555-5555-5555-555555555555",
            host="https://wheat-5111c2e081f4.herokuapp.com/api/",
            web="https://wheat-5111c2e081f4.herokuapp.com/authors/55555555-5555-5555-5555-555555555555/",
            displayName="Same Node Api Actor",
        )
        target_user = User.objects.create_user(username="same-node-api-target", password="password6")
        target = Author.objects.create(
            user=target_user,
            serial=uuid.uuid4(),
            url="https://wheat-5111c2e081f4.herokuapp.com/api/authors/66666666-6666-6666-6666-666666666666",
            host="https://wheat-5111c2e081f4.herokuapp.com/api/",
            web="https://wheat-5111c2e081f4.herokuapp.com/authors/66666666-6666-6666-6666-666666666666/",
            displayName="Same Node Api Target",
        )
        encoded_target = urllib.parse.quote(target.url, safe="")

        self.client.login(username="same-node-api-actor", password="password5")
        response = self.client.put(f"/api/authors/{actor.serial}/following/{encoded_target}")

        self.assertEqual(response.status_code, 204)
        self.assertTrue(Follow.objects.filter(actor=actor, target=target, status="REQUESTED").exists())
    
