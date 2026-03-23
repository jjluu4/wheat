from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from core.models import Author, Follow, RemoteNode
import uuid
import base64


class FollowAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.author1 = Author.objects.create(user=self.user1, displayName="user1", serial=uuid.uuid4(), url=uuid.uuid4())

        self.user2 = User.objects.create_user(username="user2", password="password2")
        self.author2 = Author.objects.create(user=self.user2, displayName="user2", serial=uuid.uuid4(), url=uuid.uuid4())

        self.user3 = User.objects.create_user(username="user3", password="password3")
        self.author3 = Author.objects.create(user=self.user3, displayName="user3", serial=uuid.uuid4(), url=uuid.uuid4())
    
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
    
    