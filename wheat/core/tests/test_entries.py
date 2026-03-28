from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.utils import timezone
import uuid, urllib, base64
from core.models import Author, Entry, Follow, RemoteNode


class AuthorsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.author = Author.objects.create(
            user=self.user,
            displayName="User1",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
            host="http://testserver/api/",
            web=f"http://testserver/authors/{uuid.uuid4()}",
        )

    def testAllAuthorsGet(self):
        """GET /api/authors returns an authors collection."""
        resp = self.client.get("/api/authors/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "authors")
        self.assertIn("authors", resp.data)
        self.assertIn("count", resp.data)
        self.assertIn("page_number", resp.data)
        self.assertIn("size", resp.data)

    def testSingleAuthorGet(self):
        """GET /api/authors/{id}/ returns a single author."""
        resp = self.client.get(f"/api/authors/{self.author.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "author")
        self.assertEqual(resp.data["displayName"], "User1")

    def test_all_authors_excludes_federated_foreign_host_authors(self):
        """Cached copies of other-node authors (different ``host``) are not in /api/authors/."""
        remote = Author.objects.create(
            displayName="RemoteOnly",
            serial=uuid.uuid4(),
            url="http://remote-node.example.com/api/authors/remote-only",
            host="http://remote-node.example.com/api/",
            web="http://remote-node.example.com/authors/remote-only",
        )

        resp = self.client.get("/api/authors/")

        self.assertEqual(resp.status_code, 200)
        author_ids = {author["id"] for author in resp.data["authors"]}
        self.assertIn(self.author.url, author_ids)
        self.assertNotIn(remote.url, author_ids)
        self.assertEqual(resp.data["count"], 1)

    def test_all_authors_excludes_inactive_local_users(self):
        inactive_user = User.objects.create_user(username="inactive", password="pass12345", is_active=False)
        inactive_author = Author.objects.create(
            user=inactive_user,
            displayName="Inactive User",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
            host="http://testserver/api/",
            web=f"http://testserver/authors/{uuid.uuid4()}",
        )

        resp = self.client.get("/api/authors/")

        self.assertEqual(resp.status_code, 200)
        author_ids = {author["id"] for author in resp.data["authors"]}
        self.assertNotIn(inactive_author.url, author_ids)

    def test_all_authors_are_ordered_by_display_name_then_serial(self):
        user_a = User.objects.create_user(username="author-a", password="pass12345")
        user_b = User.objects.create_user(username="author-b", password="pass12345")
        user_c = User.objects.create_user(username="author-c", password="pass12345")
        user_d = User.objects.create_user(username="author-d", password="pass12345")
        user_e = User.objects.create_user(username="author-e", password="pass12345")

        author_a = Author.objects.create(
            user=user_a,
            displayName="Alpha",
            serial=uuid.UUID("00000000-0000-0000-0000-000000000003"),
            url="http://testserver/api/authors/alpha-third",
            host="http://testserver/api/",
            web="http://testserver/authors/alpha-third",
        )
        author_b = Author.objects.create(
            user=user_b,
            displayName="Alpha",
            serial=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            url="http://testserver/api/authors/alpha-first",
            host="http://testserver/api/",
            web="http://testserver/authors/alpha-first",
        )
        author_c = Author.objects.create(
            user=user_c,
            displayName="Bravo",
            serial=uuid.uuid4(),
            url="http://testserver/api/authors/bravo",
            host="http://testserver/api/",
            web="http://testserver/authors/bravo",
        )
        author_d = Author.objects.create(
            user=user_d,
            displayName="Charlie",
            serial=uuid.uuid4(),
            url="http://testserver/api/authors/charlie",
            host="http://testserver/api/",
            web="http://testserver/authors/charlie",
        )
        author_e = Author.objects.create(
            user=user_e,
            displayName="Zulu",
            serial=uuid.uuid4(),
            url="http://testserver/api/authors/zulu",
            host="http://testserver/api/",
            web="http://testserver/authors/zulu",
        )

        resp = self.client.get("/api/authors/?page=1&size=5")

        self.assertEqual(resp.status_code, 200)
        returned_ids = [author["id"] for author in resp.data["authors"]]
        expected_ids = [
            author_b.url,
            author_a.url,
            author_c.url,
            author_d.url,
            self.author.url,
        ]
        self.assertEqual(returned_ids, expected_ids)
        self.assertNotIn(author_e.url, returned_ids)


class EntriesApiTests(APITestCase):
    def setUp(self):
        self.owner_user = User.objects.create_user(username="owner", password="pass12345")
        self.owner = Author.objects.create(user=self.owner_user, displayName="Owner", serial=uuid.uuid4(), url=uuid.uuid4())
        self.friend_user = User.objects.create_user(username="friend", password="pass12345")
        self.friend = Author.objects.create(user=self.friend_user, displayName="Friend", serial=uuid.uuid4(), url=uuid.uuid4())

        Follow.objects.create(actor=self.owner, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.owner, status="ACCEPTED")

        self.public_entry = Entry.objects.create(author=self.owner, url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}", content="Public entry", content_type="text/plain", visibility="PUBLIC", published=timezone.now())
        self.unlisted_entry = Entry.objects.create(author=self.owner, url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}", content="Unlisted entry", content_type="text/plain", visibility="UNLISTED", published=timezone.now())
        self.friends_entry = Entry.objects.create(author=self.owner, url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}", content="Friends entry", content_type="text/plain", visibility="FRIENDS", published=timezone.now())
        self.valid_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/BDXz4verCCMpcXxWC+YCixid+Mu9maNkCQHpN8GxHvAq2l6ZIoP8c9FwtYKXRvf0tokCXKcYA/FjP2qHJoG6TQEukT84DGn0K+qrAcb7Njtlq13Ox0rCxygUB39oHyYbYewyQARYGGz39IGxkhDUTj0wEPYcTPaZx5IbFAYByvSftPHtXMFyM6Nmuu0nN/jmLKbKZRmVAO9/B5FDLx8H1d7G7Q7YX3dKUtd6tSZe6gR80gbxFI7Ts+ktpXk2FBIKGdD8ykm0/ooBAAD//9rrXuup1DRZAAAAAElFTkSuQmCC="
        self.public_image_entry = Entry.objects.create(
            author=self.owner, 
            url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}", 
            content=f"data:image/png;base64,{self.valid_base64}", 
            content_type="image", 
            visibility="PUBLIC", 
            published=timezone.now()
        )
        
        self.friends_image_entry = Entry.objects.create(
            author=self.friend, 
            url=f"http://testserver/api/authors/{self.friend.serial}/entries/{uuid.uuid4()}", 
            content=f"data:image/png;base64,{self.valid_base64}", 
            content_type="image", 
            visibility="FRIENDS", 
            published=timezone.now()
        )
        
        self.remote_node = RemoteNode.objects.create(
            name="Remote Node",
            base_url="https://remote.example.com",
            api_base_url="https://remote.example.com/api",
            username="remote-user",
            password="remote-pass",
            is_active=True,
            notes="remote",
        )        

    def testAuthorEntriesListUnauthOnlyPublic(self):
        """Unauthenticated user sees public and unlisted entries, not friends-only."""
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "entries")
        items = resp.data.get("src") or resp.data.get("entries") or []
        contents = [entry["content"] for entry in items]
        self.assertIn("Public entry", contents)
        self.assertIn("Unlisted entry", contents)
        self.assertNotIn("Friends entry", contents)

    def testAuthorEntriesListRemoteNodeSeesPublicAndUnlisted(self):
        """Remote node Basic Auth can list public and unlisted entries without following."""
        auth = base64.b64encode("remote-user:remote-pass".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/", headers=headers)
        self.assertEqual(resp.status_code, 200)
        items = resp.data.get("src") or resp.data.get("entries") or []
        contents = [entry["content"] for entry in items]
        self.assertIn("Public entry", contents)
        self.assertIn("Unlisted entry", contents)
        self.assertNotIn("Friends entry", contents)

    def testAuthorEntriesListLoggedInNonFollowerSeesPublicAndUnlisted(self):
        """Logged-in user who does not follow the author still sees public and unlisted entries."""
        stranger_user = User.objects.create_user(username="stranger", password="pass12345")
        Author.objects.create(user=stranger_user, displayName="Stranger", serial=uuid.uuid4(), url=uuid.uuid4())
        self.client.login(username="stranger", password="pass12345")
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/")
        self.assertEqual(resp.status_code, 200)
        items = resp.data.get("src") or resp.data.get("entries") or []
        contents = [entry["content"] for entry in items]
        self.assertIn("Public entry", contents)
        self.assertIn("Unlisted entry", contents)
        self.assertNotIn("Friends entry", contents)

    def testAuthorEntriesListFollowerWithRemoteAuthGetsUnlisted(self):
        """Follower visibility is not overridden when Basic Auth is also present (session + remote)."""
        follower_user = User.objects.create_user(username="follower", password="pass12345")
        follower = Author.objects.create(user=follower_user, displayName="Follower", serial=uuid.uuid4(), url=uuid.uuid4())
        Follow.objects.create(actor=follower, target=self.owner, status="ACCEPTED")
        auth = base64.b64encode("remote-user:remote-pass".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        self.client.login(username="follower", password="pass12345")
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/", headers=headers)
        self.assertEqual(resp.status_code, 200)
        items = resp.data.get("src") or resp.data.get("entries") or []
        contents = [entry["content"] for entry in items]
        self.assertIn("Public entry", contents)
        self.assertIn("Unlisted entry", contents)
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
    
    def testSingleEntryGetFriendsWithRemoteAuth(self):
        """Fetching a friends-only entry with authentication is accepted."""
        auth = base64.b64encode("remote-user:remote-pass".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.friends_entry.serial}/", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "entry")
        self.assertEqual(resp.data["content"], "Friends entry")    

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

    def test_single_image_entry_payload_uses_canonical_image_url(self):
        """Image entry payloads expose the canonical entry image endpoint, not the raw stored image URL."""
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.public_image_entry.serial}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data["imageUrl"],
            f"{self.public_image_entry.url}/image/",
        )

    def testGetEntryByFqidPublic(self):
        """Anyone can fetch a public entry by its FQID."""
        encoded_fqid = urllib.parse.quote(self.public_entry.url, safe='')
        resp = self.client.get(f"/api/entries/{encoded_fqid}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Public entry")

    def testGetEntryByFqidFriends(self):
        """Fetching a friends-only entry by FQID respects permissions."""
        encoded_fqid = urllib.parse.quote(self.friends_entry.url, safe='')
        
        # Unauthenticated
        resp_unauth = self.client.get(f"/api/entries/{encoded_fqid}/")
        self.assertIn(resp_unauth.status_code, [401, 403])
        
        # Authenticated as friend
        self.client.login(username="friend", password="pass12345")
        resp_auth = self.client.get(f"/api/entries/{encoded_fqid}/")
        self.assertEqual(resp_auth.status_code, 200)
        self.assertEqual(resp_auth.data["content"], "Friends entry")

    def testGetAuthorImageEntry(self):
        """Fetching an image entry via author/entry serials returns raw binary."""
        
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.public_image_entry.serial}/image/")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertEqual(resp.content, base64.b64decode(self.valid_base64))
    
    def testGetFriendsImageEntryRemote(self):
        """Fetching a friends-only image entry with remote authentication returns its raw binary"""
        auth = base64.b64encode("remote-user:remote-pass".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}        
        resp = self.client.get(f"/api/authors/{self.friend.serial}/entries/{self.friends_image_entry.serial}/image/", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertEqual(resp.content, base64.b64decode(self.valid_base64))     

    def testGetFqidImageEntry(self):
        """Fetching an image entry via FQID returns raw binary."""
        encoded_fqid = urllib.parse.quote(self.public_image_entry.url, safe='')
        
        resp = self.client.get(f"/api/entries/{encoded_fqid}/image/")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertEqual(resp.content, base64.b64decode(self.valid_base64))
    
    def testGetFriendsImageEntryFqidRemote(self):
        """Fetching a friends-only image entry with remote authentication through the fqid endpoint returns its raw binary"""
        encoded_fqid = urllib.parse.quote(self.friends_image_entry.url, safe='')
        auth = base64.b64encode("remote-user:remote-pass".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}        
        resp = self.client.get(f"/api/entries/{encoded_fqid}/image/", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertEqual(resp.content, base64.b64decode(self.valid_base64))     

    def testImageEntryInvalidType(self):
        """Fetching the image endpoint on a text entry returns 404."""
        # Test standard route
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/image/")
        self.assertEqual(resp.status_code, 404)
        
        # Test FQID route
        encoded_fqid = urllib.parse.quote(self.public_entry.url, safe='')
        resp_fqid = self.client.get(f"/api/entries/{encoded_fqid}/image/")
        self.assertEqual(resp_fqid.status_code, 404)
