import base64
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
import uuid
from core.models import Author, Entry, Follow
from django.contrib.auth import get_user_model

# Tests here are mostly for APIs probably for pt1
User = get_user_model()


class AuthorProfilePageTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            url="http://testserver/api/authors/test-author",
            host="http://testserver/api/",
            displayName="Skar",
            github="",  # keep empty so tests don't try network
            description="Hello! This is my profile.",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/1",
        )

        Entry.objects.create(
            url="http://testserver/api/authors/test-author/entries/1",
            author=self.author,
            content="Public post",
            content_type="text/plain",
            visibility="PUBLIC",
            published=timezone.now(),
        )

        Entry.objects.create(
            url="http://testserver/api/authors/test-author/entries/2",
            author=self.author,
            content="Friends post",
            content_type="text/plain",
            visibility="FRIENDS",
            published=timezone.now(),
        )

        Entry.objects.create(
            url="http://testserver/api/authors/test-author/entries/3",
            author=self.author,
            content="Unlisted post",
            content_type="text/plain",
            visibility="UNLISTED",
            published=timezone.now(),
        )

        self.follower_user = User.objects.create_user(username="follower", password="pass12345")
        self.follower_author = Author.objects.create(
            user=self.follower_user,
            url="http://testserver/api/authors/follower",
            host="http://testserver/api/",
            displayName="Follower",
            github="",
            description="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/follower",
        )

        self.friend_user = User.objects.create_user(username="friend", password="pass12345")
        self.friend_author = Author.objects.create(
            user=self.friend_user,
            url="http://testserver/api/authors/friend",
            host="http://testserver/api/",
            displayName="Friend",
            github="",
            description="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/friend",
        )

        Follow.objects.create(actor=self.follower_author, target=self.author, status="ACCEPTED")
        Follow.objects.create(actor=self.friend_author, target=self.author, status="ACCEPTED")
        Follow.objects.create(actor=self.author, target=self.friend_author, status="ACCEPTED")

    def test_profile_page_shows_author_and_only_public_entries(self):
        """Profile page renders author info and only public entries for visitors."""
        resp = self.client.get(reverse("author_profile", args=[self.author.serial]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Skar")
        self.assertContains(resp, "Hello! This is my profile.")
        self.assertContains(resp, "Public post")
        self.assertNotContains(resp, "Unlisted post")
        self.assertNotContains(resp, "Friends post")

    def test_profile_page_shows_unlisted_entries_to_followers(self):
        """Accepted followers can see unlisted entries on the author's profile page."""
        self.client.force_login(self.follower_user)

        resp = self.client.get(reverse("author_profile", args=[self.author.serial]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Public post")
        self.assertContains(resp, "Unlisted post")
        self.assertNotContains(resp, "Friends post")

    def test_profile_page_shows_friends_entries_to_friends(self):
        """Mutual accepted follows can see friends-only entries on the author's profile page."""
        self.client.force_login(self.friend_user)

        resp = self.client.get(reverse("author_profile", args=[self.author.serial]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Public post")
        self.assertContains(resp, "Unlisted post")
        self.assertContains(resp, "Friends post")


class AuthorEditPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="skar", password="pass12345")

        self.author = Author.objects.create(
            user=self.user,  # IMPORTANT: link author to logged-in user
            url="http://testserver/api/authors/test-author",
            host="http://testserver/api/",
            displayName="Skar",
            github="https://github.com/example",
            description="Hello! This is my profile.",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/test-author",
        )

    def test_edit_page_post_updates_author_and_redirects(self):
        """Authenticated owner can edit their profile via POST and is redirected."""
        self.client.force_login(self.user)  # IMPORTANT: login before POST

        edit_url = reverse("author_edit", args=[self.author.serial])

        resp = self.client.post(
            edit_url,
            data={
                "displayName": "Skar Test",
                "github": "https://github.com/skar-test",
                "description": "Updated description",
                "profileImage": "https://placehold.co/200x200.png",
            },
        )

        # should redirect back to the profile page after save
        self.assertEqual(resp.status_code, 302)

        # confirm the DB actually changed
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, "Skar Test")
        self.assertEqual(self.author.github, "https://github.com/skar-test")
        self.assertEqual(self.author.description, "Updated description")
        self.assertEqual(self.author.profileImage, "https://placehold.co/200x200.png")


class GitHubAutoImportTests(TestCase):
    @patch("core.views.author_views.fetch_public_events")
    def test_profile_page_auto_imports_github_events_without_duplicates(self, mock_fetch):
        """Profile page imports GitHub events once and avoids duplicates."""
        mock_fetch.return_value = [
            {
                "id": "111",
                "type": "PushEvent",
                "actor": {"login": "torvalds"},
                "repo": {"name": "torvalds/linux"},
                "payload": {"commits": []},
                "created_at": "2026-03-01T00:00:00Z",
            },
            {
                "id": "222",
                "type": "PushEvent",
                "actor": {"login": "torvalds"},
                "repo": {"name": "torvalds/linux"},
                "payload": {"commits": []},
                "created_at": "2026-03-01T00:05:00Z",
            },
        ]

        author = Author.objects.create(
            url="http://testserver/api/authors/1",
            host="http://testserver/api/",
            displayName="Skar",
            github="https://github.com/torvalds",
            description="",
            profileImage="https://example.com/p.png",
            web="http://testserver/authors/1",
        )

        url = reverse("author_profile", args=[author.serial])

        before = Entry.objects.filter(author=author).count()

        self.client.get(url)
        mock_fetch.assert_called()
        after_first = Entry.objects.filter(author=author).count()

        self.assertEqual(after_first, before + 2)

        self.client.get(url)
        after_second = Entry.objects.filter(author=author).count()
        self.assertEqual(after_second, after_first)


class AuthorListPageTests(TestCase):
    def test_author_list_page(self):
        """Author list page renders existing authors."""
        Author.objects.create(
            url="http://testserver/api/authors/test-author",
            host="http://testserver/api/",
            displayName="Skar",
            github="https://github.com/example",
            description="Hi",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/1",
        )
        resp = self.client.get(reverse("author_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Skar")

    def test_author_list_page_wraps_long_names_with_author_card_class(self):
        long_name = "DanielFromWheatOnTealNodeWithVeryLongDisplayName"
        Author.objects.create(
            url="http://testserver/api/authors/long-author",
            host="http://testserver/api/",
            displayName=long_name,
            github="https://github.com/example",
            description="Long author",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/long-author",
        )

        resp = self.client.get(reverse("author_list"))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, long_name)
        self.assertContains(resp, 'class="profile-link author-card-name"')
        self.assertContains(resp, 'class="pager-meta author-node-meta"')

    def test_open_remote_author_requires_fqid(self):
        resp = self.client.get(reverse("author_open_remote"))
        self.assertEqual(resp.status_code, 400)

    def test_open_remote_author_redirects_to_local_profile(self):
        """Catalog should link here so Follow uses this node; resolve_remote_author upserts then we redirect."""
        from unittest.mock import patch

        remote = Author.objects.create(
            url="http://remote.example/api/authors/r1",
            host="http://remote.example/api/",
            displayName="Remote",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://remote.example/authors/r1/",
        )
        with patch("core.views.author_views.resolve_remote_author", return_value=remote):
            resp = self.client.get(
                reverse("author_open_remote") + "?fqid=" + "http://remote.example/api/authors/r1"
            )
        self.assertRedirects(resp, reverse("author_profile", args=[remote.serial]), fetch_redirect_response=False)


class EntryCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.author = Author.objects.create(
            user=self.user,
            url="http://testserver/api/authors/owner-uuid",
            host="http://testserver/api/",
            displayName="Owner",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/owner-uuid/",
        )

    def test_owner_can_create_plain_text_entry(self):
        """Owner can create a plain text entry via the HTML form."""
        self.client.force_login(self.user)
        url = reverse("entry_create", args=[self.author.serial])
        resp = self.client.post(
            url,
            data={
                "content": "Hello world",
                "content_type": "text/plain",
                "image_url": "",
                "visibility": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Entry.objects.filter(author=self.author).count(), 1)
        entry = Entry.objects.get(author=self.author)
        self.assertEqual(entry.content, "Hello world")
        self.assertEqual(entry.content_type, "text/plain")

    def test_owner_can_create_markdown_entry(self):
        """Owner can create a markdown entry via the HTML form."""
        self.client.force_login(self.user)
        url = reverse("entry_create", args=[self.author.serial])
        resp = self.client.post(
            url,
            data={
                "content": "**bold** and [link](https://x.com)",
                "content_type": "text/markdown",
                "image_url": "",
                "visibility": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 302)
        entry = Entry.objects.get(author=self.author)
        self.assertEqual(entry.content_type, "text/markdown")

    def test_owner_can_create_image_entry_with_image_url(self):
        """Owner can create an image entry when an image file is uploaded."""
        self.client.force_login(self.user)
        url = reverse("entry_create", args=[self.author.serial])
        image = SimpleUploadedFile(
            "photo.gif",
            base64.b64decode("R0lGODdhAQABAIABAP///wAAACwAAAAAAQABAAACAkQBADs="),
            content_type="image/gif",
        )
        resp = self.client.post(
            url,
            data={
                "content": "My photo",
                "content_type": "image",
                "uploaded_image": image,
                "visibility": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 302)
        entry = Entry.objects.get(author=self.author)
        self.assertEqual(entry.content_type, "image")
        self.assertTrue(entry.image_url)

    def test_image_entry_requires_image_url(self):
        """Image entry creation fails if no image file is uploaded."""
        self.client.force_login(self.user)
        url = reverse("entry_create", args=[self.author.serial])
        resp = self.client.post(
            url,
            data={
                "content": "No url",
                "content_type": "image",
                "visibility": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please upload an image or change entry type")
        self.assertEqual(Entry.objects.filter(author=self.author).count(), 0)

    def test_non_owner_cannot_create_entry(self):
        """Non-owner cannot create an entry on someone else's profile."""
        other = User.objects.create_user(username="other", password="pass12345")
        self.client.force_login(other)
        url = reverse("entry_create", args=[self.author.serial])
        resp = self.client.post(
            url,
            data={
                "content": "Hacked",
                "content_type": "text/plain",
                "image_url": "",
                "visibility": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Entry.objects.filter(author=self.author).count(), 0)

    def test_create_entry_redirects_to_profile(self):
        """Successful entry creation redirects back to the author's profile."""
        self.client.force_login(self.user)
        url = reverse("entry_create", args=[self.author.serial])
        resp = self.client.post(
            url,
            data={
                "content": "Done",
                "content_type": "text/plain",
                "image_url": "",
                "visibility": "PUBLIC",
            },
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("author_profile", args=[self.author.serial]))
        
    @patch("core.federation.send_to_author_inbox")
    def test_create_entry_sends_to_remote_entry_authors(self, mock_send):
        '''Creating a new entry sends that entry to the inboxes of all remote followers'''
        mock_send.return_value = True, None
        
        remote_follower = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-follower",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote follower",
            github="",
            profileImage="https://example.com/image.png",
            web="http://remote-node-a.example.com/authors/remote-follower/",
        )
        
        Follow.objects.create(actor=remote_follower, target=self.author, status="ACCEPTED")
        
        self.client.force_login(self.user)
        url = reverse("entry_create", args=[self.author.serial])
        resp = self.client.post(
            url,
            data={
                "content": "Creating entry should post to inbox",
                "content_type": "text/plain",
                "image_url": "",
                "visibility": "UNLISTED",
            },
        )
        self.assertEqual(resp.status_code, 302)
        mock_send.assert_called_once()
        #print(mock_send.call_args.args[0])
        self.assertEqual(mock_send.call_args.args[0], remote_follower)
        self.assertEqual(mock_send.call_args.args[1]['content'], 'Creating entry should post to inbox')        


class EntryEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.author = Author.objects.create(
            user=self.user,
            url="http://testserver/api/authors/owner-uuid",
            host="http://testserver/api/",
            displayName="Owner",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/owner-uuid/",
        )
        self.entry = Entry.objects.create(
            url="http://testserver/api/authors/owner-uuid/entries/e1",
            author=self.author,
            content="Original",
            content_type="text/plain",
            visibility="PUBLIC",
            published=timezone.now(),
        )
        self.entryForFollower = Entry.objects.create(
            url="http://testserver/api/authors/owner-uuid/entries/e2",
            author=self.author,
            content="Remote",
            content_type="text/plain",
            visibility="UNLISTED",
            published=timezone.now(),
        )   

    def test_owner_can_edit_entry(self):
        """Owner can edit an existing entry via the HTML form."""
        self.client.force_login(self.user)
        url = reverse("entry_edit", args=[self.author.serial, self.entry.serial])
        resp = self.client.post(
            url,
            data={
                "content": "Updated content",
                "content_type": "text/plain",
                "image_url": "",
                "visibility": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.content, "Updated content")

    def test_non_owner_cannot_edit_entry(self):
        """Non-owner cannot edit another author's entry."""
        other = User.objects.create_user(username="other", password="pass12345")
        self.client.force_login(other)
        url = reverse("entry_edit", args=[self.author.serial, self.entry.serial])
        resp = self.client.post(
            url,
            data={
                "content": "Hacked",
                "content_type": "text/plain",
                "image_url": "",
                "visibility": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 403)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.content, "Original")
        
    @patch("core.federation.send_to_author_inbox")
    def test_edit_entry_sends_to_remote_entry_authors(self, mock_send):
        '''Editing an entry updates that entry in the inboxes of all remote followers'''
        mock_send.return_value = True, None
        
        remote_follower = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-follower",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote follower",
            github="",
            profileImage="https://example.com/image.png",
            web="http://remote-node-a.example.com/authors/remote-follower/",
        )
        
        Follow.objects.create(actor=remote_follower, target=self.author, status="ACCEPTED")
        
        self.client.force_login(self.user)
        url = reverse("entry_edit", args=[self.author.serial, self.entryForFollower.serial])
        resp = self.client.post(
            url,
            data={
                "content": "Editing entry should post to inbox",
                "content_type": "text/plain",
                "image_url": "",
                "visibility": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 302)
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], remote_follower)
        self.assertEqual(mock_send.call_args.args[1]["content"], "Editing entry should post to inbox")


class EntryDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.author = Author.objects.create(
            user=self.user,
            url="http://testserver/api/authors/owner-uuid",
            host="http://testserver/api/",
            displayName="Owner",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/owner-uuid/",
        )
        self.entry = Entry.objects.create(
            url="http://testserver/api/authors/owner-uuid/entries/e1",
            author=self.author,
            content="To delete",
            content_type="text/plain",
            visibility="PUBLIC",
            published=timezone.now(),
        )
        self.entryForFollower = Entry.objects.create(
            url="http://testserver/api/authors/owner-uuid/entries/e2",
            author=self.author,
            content="Remote",
            content_type="text/plain",
            visibility="UNLISTED",
            published=timezone.now(),
        )  

    def test_owner_can_delete_entry_soft_delete(self):
        """Owner can soft-delete an entry from their profile."""
        self.client.force_login(self.user)
        url = reverse("entry_delete", args=[self.author.serial, self.entry.serial])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.visibility, "DELETED")

    def test_repeated_delete_submit_is_safe_no_op_for_owner(self):
        self.client.force_login(self.user)
        url = reverse("entry_delete", args=[self.author.serial, self.entry.serial])

        first_response = self.client.post(url)
        second_response = self.client.post(url)

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.visibility, "DELETED")

    def test_non_owner_cannot_delete_entry(self):
        """Non-owner cannot delete another author's entry."""
        other = User.objects.create_user(username="other", password="pass12345")
        self.client.force_login(other)
        url = reverse("entry_delete", args=[self.author.serial, self.entry.serial])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.visibility, "PUBLIC")

    def test_deleted_entry_not_on_owner_profile(self):
        """Soft-deleted entries no longer appear on the owner's profile."""
        self.entry.visibility = "DELETED"
        self.entry.save(update_fields=["visibility"])
        self.client.force_login(self.user)
        resp = self.client.get(reverse("author_profile", args=[self.author.serial]))
        self.assertNotContains(resp, "To delete")
    
    @patch("core.federation.send_to_author_inbox")
    def test_delete_entry_updates_remote_entry_authors(self, mock_send):
        '''Deleting an entry sends an update for that entry to the inboxes of all remote followers'''
        mock_send.return_value = True, None
        
        remote_follower = Author.objects.create(
            serial=uuid.uuid4(),
            url="http://remote-node-a.example.com/api/authors/remote-follower",
            host="http://remote-node-a.example.com/api/",
            displayName="Remote follower",
            github="",
            profileImage="https://example.com/image.png",
            web="http://remote-node-a.example.com/authors/remote-follower/",
        )
        
        Follow.objects.create(actor=remote_follower, target=self.author, status="ACCEPTED")
        
        self.client.force_login(self.user)
        url = reverse("entry_delete", args=[self.author.serial, self.entryForFollower.serial])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        mock_send.assert_called_once()
        #print(mock_send.call_args_list)
        self.assertEqual(mock_send.call_args.args[0], remote_follower)
        self.assertEqual(mock_send.call_args.args[1]["visibility"], "DELETED")    


class EntryViewPageInteractionTests(TestCase):
    def setUp(self):
        self.owner_user = User.objects.create_user(username="owner-view", password="pass12345")
        self.viewer_user = User.objects.create_user(username="viewer-view", password="pass12345")
        self.friend_user = User.objects.create_user(username="friend-view", password="pass12345")

        self.owner = Author.objects.create(
            user=self.owner_user,
            url="http://testserver/api/authors/owner-view",
            host="http://testserver/api/",
            displayName="OwnerView",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/owner-view/",
        )
        self.viewer = Author.objects.create(
            user=self.viewer_user,
            url="http://testserver/api/authors/viewer-view",
            host="http://testserver/api/",
            displayName="ViewerView",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/viewer-view/",
        )
        self.friend = Author.objects.create(
            user=self.friend_user,
            url="http://testserver/api/authors/friend-view",
            host="http://testserver/api/",
            displayName="FriendView",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/friend-view/",
        )

        from core.models import Follow

        Follow.objects.create(actor=self.owner, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.owner, status="ACCEPTED")

        self.public_entry = Entry.objects.create(
            url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}",
            author=self.owner,
            title="Public view entry",
            content="Visible on entry page",
            content_type="text/plain",
            visibility="PUBLIC",
            published=timezone.now(),
        )
        self.friends_entry = Entry.objects.create(
            url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}",
            author=self.owner,
            title="Friends view entry",
            content="Friends only on entry page",
            content_type="text/plain",
            visibility="FRIENDS",
            published=timezone.now(),
        )

    def test_authenticated_viewer_sees_like_and_comment_controls_on_public_entry_page(self):
        """Authenticated viewer sees like/comment UI on a public entry page."""
        self.client.force_login(self.viewer_user)
        resp = self.client.get(reverse("view_entry", args=[self.owner.serial, self.public_entry.serial]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "toggleLike")
        self.assertContains(resp, "Comments")
        self.assertContains(resp, "Comment")
        self.assertContains(resp, "entry.js?v=likes-ui-4")

    def test_friend_sees_like_and_comment_controls_on_friends_entry_page(self):
        """Friend sees like/comment UI on a friends-only entry page."""
        self.client.force_login(self.friend_user)
        resp = self.client.get(reverse("view_entry", args=[self.owner.serial, self.friends_entry.serial]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "toggleLike")
        self.assertContains(resp, "Comments")


class EntryProfileVisibilityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.author = Author.objects.create(
            user=self.owner,
            url="http://testserver/api/authors/owner-uuid",
            host="http://testserver/api/",
            displayName="Owner",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/owner-uuid/",
        )
        Entry.objects.create(
            url="http://testserver/api/authors/owner-uuid/entries/1",
            author=self.author,
            content="Public entry",
            content_type="text/plain",
            visibility="PUBLIC",
            published=timezone.now(),
        )
        Entry.objects.create(
            url="http://testserver/api/authors/owner-uuid/entries/2",
            author=self.author,
            content="Unlisted entry",
            content_type="text/plain",
            visibility="UNLISTED",
            published=timezone.now(),
        )

    def test_visitor_sees_only_public_entries(self):
        """Visitor sees only public entries on an author's profile."""
        resp = self.client.get(reverse("author_profile", args=[self.author.serial]))
        self.assertContains(resp, "Public entry")
        self.assertNotContains(resp, "Unlisted entry")

    def test_owner_sees_all_non_deleted_entries(self):
        """Owner sees all non-deleted entries on their own profile."""
        self.client.force_login(self.owner)
        resp = self.client.get(reverse("author_profile", args=[self.author.serial]))
        self.assertContains(resp, "Public entry")
        self.assertContains(resp, "Unlisted entry")

    def test_owner_sees_new_entry_and_edit_delete_links(self):
        """Owner sees controls to create, edit, and delete entries."""
        self.client.force_login(self.owner)
        resp = self.client.get(reverse("author_profile", args=[self.author.serial]))
        self.assertContains(resp, "New entry")
        self.assertContains(resp, "Edit")
        self.assertContains(resp, "Delete")

    def test_visitor_does_not_see_new_entry_or_edit_delete(self):
        """Visitor does not see entry creation or edit/delete controls."""
        resp = self.client.get(reverse("author_profile", args=[self.author.serial]))
        self.assertNotContains(resp, "New entry")
        self.assertNotContains(resp, "Edit profile")


class AuthorProfileFriendsVisibilityTests(TestCase):
    """Friends-only entries appear on HTML profile for mutual friends (matches stream rules)."""

    def setUp(self):
        self.owner_user = User.objects.create_user(username="apf-owner", password="pass12345")
        self.friend_user = User.objects.create_user(username="apf-friend", password="pass12345")
        self.stranger_user = User.objects.create_user(username="apf-stranger", password="pass12345")
        self.owner = Author.objects.create(
            user=self.owner_user,
            url="http://testserver/api/authors/apf-owner",
            host="http://testserver/api/",
            displayName="APFOwner",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/apf-owner/",
        )
        self.friend = Author.objects.create(
            user=self.friend_user,
            url="http://testserver/api/authors/apf-friend",
            host="http://testserver/api/",
            displayName="APFFriend",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/apf-friend/",
        )
        from core.models import Follow

        Follow.objects.create(actor=self.owner, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.owner, status="ACCEPTED")

        self.friends_only = Entry.objects.create(
            url=f"http://testserver/api/authors/{self.owner.serial}/entries/{uuid.uuid4()}",
            author=self.owner,
            title="Friends only profile",
            content="Secret for mutual friends",
            content_type="text/plain",
            visibility="FRIENDS",
            published=timezone.now(),
        )

    def test_mutual_friend_sees_friends_entry_on_profile(self):
        self.client.force_login(self.friend_user)
        resp = self.client.get(reverse("author_profile", args=[self.owner.serial]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Secret for mutual friends")

    def test_stranger_does_not_see_friends_entry_on_profile(self):
        self.client.force_login(self.stranger_user)
        resp = self.client.get(reverse("author_profile", args=[self.owner.serial]))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Secret for mutual friends")


class StreamDeletedEntryVisibilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="stream-owner", password="pass12345")
        self.author = Author.objects.create(
            user=self.user,
            url="http://testserver/api/authors/stream-owner",
            host="http://testserver/api/",
            displayName="StreamOwner",
            github="",
            profileImage="https://placehold.co/150x150.png",
            web="http://testserver/authors/stream-owner/",
        )
        Entry.objects.create(
            url="http://testserver/api/authors/stream-owner/entries/live",
            author=self.author,
            title="Live entry",
            content="Visible stream content",
            content_type="text/plain",
            visibility="PUBLIC",
            published=timezone.now(),
        )
        Entry.objects.create(
            url="http://testserver/api/authors/stream-owner/entries/deleted",
            author=self.author,
            title="Deleted entry",
            content="Should not appear",
            content_type="text/plain",
            visibility="DELETED",
            published=timezone.now(),
        )

    def test_owner_stream_excludes_soft_deleted_entries(self):
        """Owner stream excludes entries marked DELETED."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("my_stream"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Visible stream content")
        self.assertNotContains(resp, "Should not appear")
