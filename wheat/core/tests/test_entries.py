from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from core.models import Author, Entry, Follow


class AuthorsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.author = Author.objects.create(user=self.user, displayName="User1", serial=uuid.uuid4(), url=uuid.uuid4())

    def testAllAuthorsGet(self):
        """GET /api/authors returns an authors collection."""
        resp = self.client.get("/api/authors")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "authors")
        self.assertIn("authors", resp.data)

    def testSingleAuthorGet(self):
        """GET /api/authors/{id}/ returns a single author."""
        resp = self.client.get(f"/api/authors/{self.author.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "author")
        self.assertEqual(resp.data["displayName"], "User1")


class EntriesApiTests(APITestCase):
    def setUp(self):
        self.owner_user = User.objects.create_user(username="owner", password="pass12345")
        self.owner = Author.objects.create(user=self.owner_user, displayName="Owner", serial=uuid.uuid4(), url=uuid.uuid4())
        self.friend_user = User.objects.create_user(username="friend", password="pass12345")
        self.friend = Author.objects.create(user=self.friend_user, displayName="Friend", serial=uuid.uuid4(), url=uuid.uuid4())

        Follow.objects.create(actor=self.owner, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.owner, status="ACCEPTED")

        self.public_entry = Entry.objects.create(author=self.owner, url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}", content="Public entry", content_type="text/plain", visibility="PUBLIC", published=timezone.now())
        self.friends_entry = Entry.objects.create(author=self.owner, url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}", content="Friends entry", content_type="text/plain", visibility="FRIENDS", published=timezone.now())

    def testAuthorEntriesListUnauthOnlyPublic(self):
        """Unauthenticated user sees only public entries in author entries list."""
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "entries")
        items = resp.data.get("src") or resp.data.get("entries") or []
        contents = [entry["content"] for entry in items]
        self.assertIn("Public entry", contents)
        self.assertNotIn("Friends entry", contents)

    def testAuthorEntriesListFriendSeesFriends(self):
        """Friend can see public and friends-only entries in author entries list."""
        self.client.login(username="friend", password="pass12345")
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/")
        self.assertEqual(resp.status_code, 200)
        items = resp.data.get("src") or resp.data.get("entries") or []
        contents = [entry["content"] for entry in items]
        self.assertIn("Public entry", contents)
        self.assertIn("Friends entry", contents)

    def testSingleEntryGetPublicUnauth(self):
        """Unauthenticated user can fetch a single public entry."""
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "entry")
        self.assertEqual(resp.data["content"], "Public entry")

    def testSingleEntryGetFriendsRequiresAuth(self):
        """Fetching a friends-only entry without authentication is rejected."""
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/")
        self.assertEqual(resp.status_code, 401)

    def testSingleEntryGetFriendsFriendCanView(self):
        """Friend can fetch a friends-only entry."""
        self.client.login(username="friend", password="pass12345")
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Friends entry")

    def testOwnerCanCreateEntryViaApi(self):
        """Entry owner can create entries via the API."""
        self.client.login(username="owner", password="pass12345")
        payload = {
            "content": "Created via API",
            "contentType": "text/markdown",
            "visibility": "PUBLIC",
            "imageUrl": "",
        }
        resp = self.client.post(f"/api/authors/{self.owner.serial}/entries/", data=payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["content"], "Created via API")
        self.assertEqual(resp.data["contentType"], "text/markdown")

    def testNonOwnerCannotCreateEntryViaApi(self):
        """Non-owner cannot create entries for another author via the API."""
        self.client.login(username="friend", password="pass12345")
        payload = {"content": "Nope", "contentType": "text/plain", "visibility": "PUBLIC"}
        resp = self.client.post(f"/api/authors/{self.owner.serial}/entries/", data=payload, format="json")
        self.assertEqual(resp.status_code, 403)

    def testOwnerCanEditEntryViaApi(self):
        """Entry owner can update their entry via the API."""
        self.client.login(username="owner", password="pass12345")
        payload = {"content": "Updated via API", "contentType": "text/plain", "visibility": "PUBLIC"}
        resp = self.client.put(
            f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/",
            data=payload,
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Updated via API")

    def testOwnerCanDeleteEntry(self):
        """Entry owner can soft-delete an entry via the API."""
        self.client.login(username="owner", password="pass12345")
        resp = self.client.delete(f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/")
        self.assertEqual(resp.status_code, 204)
        self.public_entry.refresh_from_db()
        self.assertEqual(self.public_entry.visibility, "DELETED")

