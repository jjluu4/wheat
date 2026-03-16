from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Author, Entry, Follow
from django.utils import timezone
import uuid


class LinkVisibilityTest(TestCase):
    # These tests are specifically for ensuring that visibilites behave correctly for shared entry links.
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.author1 = Author.objects.create(user=self.user1, displayName="user1", serial=uuid.uuid4(), url=f"http://testserver/api/authors/{uuid.uuid4()}")

        self.user2 = User.objects.create_user(username="user2", password="password2")
        self.author2 = Author.objects.create(user=self.user2, displayName="user2", serial=uuid.uuid4(), url=f"http://testserver/api/authors/{uuid.uuid4()}")

        self.user3 = User.objects.create_user(username="user3", password="password3")
        self.author3 = Author.objects.create(user=self.user3, displayName="user3", serial=uuid.uuid4(), url=f"http://testserver/api/authors/{uuid.uuid4()}")
    
        # User 1 and User 2 are friends
        Follow.objects.create(actor=self.author2, target=self.author1, status="ACCEPTED")
        Follow.objects.create(actor=self.author1, target=self.author2, status="ACCEPTED")

        self.public_entry = Entry.objects.create(
            author=self.author1,
            serial=uuid.uuid4(), 
            url=f"http://testserver/authors/{self.author1.serial}/entries/{uuid.uuid4()}", 
            content="Public entry", 
            content_type="text/plain", visibility="PUBLIC", 
            published=timezone.now()
        )

        self.unlisted_entry = Entry.objects.create(
            author=self.author1,
            serial=uuid.uuid4(), 
            url=f"http://testserver/authors/{self.author1.serial}/entries/{uuid.uuid4()}", 
            content="Unlisted entry", 
            content_type="text/plain", 
            visibility="UNLISTED", 
            published=timezone.now()
        )

        self.friends_entry = Entry.objects.create(
            author=self.author1,
            serial=uuid.uuid4(),
            url=f"http://testserver/authors/{self.author1.serial}/entries/{uuid.uuid4()}/", 
            content="Friends entry", 
            content_type="text/plain", 
            visibility="FRIENDS", 
            published=timezone.now() 
        )

    def test_unauthenticated_public_visibility(self):
        # Test that unauthenticated users can view public entries via a shared link.
        response = self.client.get(f"/authors/{self.author1.serial}/entries/{self.public_entry.serial}/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        self.assertIn(self.public_entry.content, content)

    def test_unauthenticated_unlisted_visibility(self):
        # Test that unauthenticated users can view unlisted entries via a shared link.
        response = self.client.get(f"/authors/{self.author1.serial}/entries/{self.unlisted_entry.serial}/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        self.assertIn(self.unlisted_entry.content, content)

    def test_unauthenticated_friend_visibility(self):
        # Test that unauthenticated users cannot view friend-only entries via a shared link.
        response = self.client.get(f"/authors/{self.author1.serial}/entries/{self.friends_entry.serial}/")
        self.assertEqual(response.status_code, 403)

        content = response.content.decode("utf-8")
        self.assertNotIn(self.friends_entry.content, content)
    
    def test_authenticated_friend_visibility(self):
        # Test that authenticated users can view friend-only posts if they are friends with the author via a shared link.
        self.client.login(username="user2", password="password2")
        response = self.client.get(f"/authors/{self.author1.serial}/entries/{self.friends_entry.serial}/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        self.assertIn(self.friends_entry.content, content)

    def test_authenticated_nonfriend_visibility(self):
        # Test that authenticated users cannot view friend-only posts if they are not friends with the author via a shared link.
        self.client.login(username="user3", password="password3")
        response = self.client.get(f"/authors/{self.author1.serial}/entries/{self.friends_entry.serial}/")
        self.assertEqual(response.status_code, 403)

        content = response.content.decode("utf-8")
        self.assertNotIn(self.friends_entry.content, content)