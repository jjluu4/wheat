from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from core.models import Author, Follow
import uuid


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

    def testFollowingList(self):
        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/following")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'following')

        following = [author['displayName'] for author in response.data['following']]

        self.assertIn(self.author3.displayName, following)
        self.assertNotIn(self.author2.displayName, following)
    
    def testFollowRequests(self):
        self.client.login(username="user1", password="password1")
        response = self.client.get(f"/api/authors/{self.author1.serial}/follow_requests")

        self.assertEqual(response.status_code, 200)

        followRequests = [item['actor']['displayName'] for item in response.data]

        self.assertIn(self.author2.displayName, followRequests)
        self.assertNotIn(self.author3.displayName, followRequests)
    
    