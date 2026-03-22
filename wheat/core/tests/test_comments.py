from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from core.models import Author, Comment, Entry, Follow


class CommentsAPITests(APITestCase):
    def setUp(self):
        self.owner_user = User.objects.create_user(username="owner", password="pass12345")
        self.friend_user = User.objects.create_user(username="friend", password="pass12345")
        self.stranger_user = User.objects.create_user(username="stranger", password="pass12345")
        self.former_user = User.objects.create_user(username="former", password="pass12345")

        self.owner = self.make_author(self.owner_user, "Owner")
        self.friend = self.make_author(self.friend_user, "Friend")
        self.stranger = self.make_author(self.stranger_user, "Stranger")
        self.former = self.make_author(self.former_user, "Former")

        Follow.objects.create(actor=self.owner, target=self.friend, status="ACCEPTED")
        Follow.objects.create(actor=self.friend, target=self.owner, status="ACCEPTED")

        self.public_entry = self.make_entry(self.owner, "Public entry", visibility="PUBLIC")
        self.friends_entry = self.make_entry(self.owner, "Friends entry", visibility="FRIENDS")
        self.unlisted_entry = self.make_entry(self.owner, "Unlisted entry", visibility="UNLISTED")

        self.public_comment = self.make_comment(self.friend, self.public_entry, "Public comment")
        self.friend_comment = self.make_comment(self.friend, self.friends_entry, "Friends only comment")
        self.former_comment = self.make_comment(self.former, self.friends_entry, "Former friend comment")
        self.owner_comment = self.make_comment(self.owner, self.public_entry, "Owner comment")

    def make_author(self, user, display_name):
        serial = uuid.uuid4()
        return Author.objects.create(
            user=user,
            serial=serial,
            url=f"http://testserver/api/authors/{serial}",
            host="http://testserver/api/",
            displayName=display_name,
            github="",
            profileImage="https://example.com/image.png",
            web=f"http://testserver/authors/{serial}/",
        )

    def make_entry(self, author, content, visibility="PUBLIC"):
        serial = uuid.uuid4()
        return Entry.objects.create(
            author=author,
            serial=serial,
            url=f"http://testserver/api/authors/{author.serial}/entries/{serial}/",
            title="Untitled",
            content=content,
            content_type="text/plain",
            visibility=visibility,
            published=timezone.now(),
        )

    def make_comment(self, author, entry, content):
        serial = uuid.uuid4()
        return Comment.objects.create(
            author=author,
            entry=entry,
            serial=serial,
            url=f"http://testserver/api/authors/{author.serial}/commented/{serial}/",
            content_type="text/plain",
            content=content,
            published=timezone.now(),
        )

    def author_commented_url(self, author):
        return f"/api/authors/{author.serial}/commented/"

    def author_commented_single_url(self, author, comment):
        return f"/api/authors/{author.serial}/commented/{comment.serial}/"

    def entry_comments_url(self, entry):
        return f"/api/authors/{entry.author.serial}/entries/{entry.serial}/comments/"

    # GET /authors/{author_serial}/commented/ tests VVV

    def test_author_commented_get_with_pagination(self):
        """Author commented GET respects pagination parameters"""
        for i in range(5):
            self.make_comment(self.friend, self.public_entry, f"Comment {i}")

        self.client.force_login(self.friend_user)
        resp = self.client.get(f"{self.author_commented_url(self.friend)}?page=1&size=3")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["page_number"], 1)
        self.assertEqual(resp.data["size"], 3)
        self.assertEqual(len(resp.data["src"]), 3)

    def test_author_commented_get_friend_sees_friends_comments(self):
        """Friend can see other friend's comments on friends only entries"""
        self.client.force_login(self.friend_user)
        resp = self.client.get(self.author_commented_url(self.owner))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["src"][0]["content"], "Owner comment")

    # POST /authors/{author_serial}/commented/ tests VVV

    def test_author_commented_post_creates_comment(self):
        """Authenticated user can create a comment on a visible entry"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "content": "New comment",
                "contentType": "text/plain",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["content"], "New comment")
        self.assertEqual(resp.data["author"]["displayName"], "Friend")

        comment = Comment.objects.get(content="New comment")
        self.assertEqual(comment.author, self.friend)
        self.assertEqual(comment.entry, self.public_entry)

    def test_author_commented_post_requires_authentication(self):
        """POST requires authentication"""
        resp = self.client.post(
            self.author_commented_url(self.stranger),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "content": "Unauthenticated comment",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 401)

    def test_author_commented_post_cannot_post_as_another_author(self):
        """User cannot post comments as another author"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.stranger),  # try to post as stranger
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "content": "impersonation",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_author_commented_post_requires_comment_text(self):
        """Comment text is required"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
            },
            format="json",
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"], "Comment text is required")

    def test_author_commented_post_requires_entry_url(self):
        """Entry URL is required"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "content": "no url",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"], "Entry URL is required")

    def test_author_commented_post_validates_entry_url_format(self):
        """Entry URL must be in the correct format"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": "invalid url",
                "content": "invalid url",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"], "Invalid entry URL format")

    def test_author_commented_post_requires_permission_to_view_entry(self):
        """Cannot comment on entry without permission to view it"""
        self.client.force_login(self.stranger_user)
        resp = self.client.post(
            self.author_commented_url(self.stranger),
            data={
                "type": "comment",
                "entry": self.friends_entry.url,
                "content": "should be blocked",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_author_commented_post_accepts_comment_field(self):
        """POST accepts 'comment' field (alias for content)"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "comment": "Using comment field",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["content"], "Using comment field")

    def test_author_commented_post_accepts_form_data(self):
        """POST accepts form-encoded data"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "content": "Form data comment",
            },
            format="multipart",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["content"], "Form data comment")

    def test_author_commented_post_rejects_wrong_type(self):
        """Type must be 'comment'"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "post",
                "entry": self.public_entry.url,
                "content": "Wrong type",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"], "Type must be 'comment'")

    def test_author_commented_post_returns_comment_payload(self):
        """Successful POST returns comment payload with all fields"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "content": "Full payload test",
                "contentType": "text/markdown",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201)
        self.assertIn("id", resp.data)
        self.assertIn("url", resp.data)
        self.assertIn("published", resp.data)
        self.assertEqual(resp.data["contentType"], "text/markdown")
        self.assertEqual(resp.data["content"], "Full payload test")

    def test_author_commented_post_friend_comments_on_friends_entry(self):
        """Friend can comment on friends only entry"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.friends_entry.url,
                "content": "Friend comment on friends entry",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201)

    def test_author_commented_post_owner_comments_on_own_entry(self):
        """Entry owner can comment on their own entry"""
        self.client.force_login(self.owner_user)
        resp = self.client.post(
            self.author_commented_url(self.owner),
            data={
                "type": "comment",
                "entry": self.friends_entry.url,
                "content": "Owner comment",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201)

    # GET /authors/{author_serial}/commented/{comment_serial}/ tests VVV
    
    def test_author_commented_single_get_returns_comment(self):
        """GET returns single comment payload"""
        self.client.force_login(self.friend_user)
        resp = self.client.get(self.author_commented_single_url(self.friend, self.friend_comment))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Friends only comment")
        self.assertIn("web", resp.data)
        self.assertEqual(resp.data["author"]["displayName"], "Friend")

    def test_author_commented_single_get_checks_permissions(self):
        """GET respects comment visibility permissions"""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.author_commented_single_url(self.friend, self.friend_comment))

        self.assertEqual(resp.status_code, 403)

    def test_author_commented_single_get_author_can_view_own_hidden_comment(self):
        """Comment author can view their own hidden comment"""
        self.client.force_login(self.former_user)
        resp = self.client.get(self.author_commented_single_url(self.former, self.former_comment))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Former friend comment")

    def test_author_commented_single_get_friend_can_view_comment_on_friends_entry(self):
        """Friend can view comment on friends only entry"""
        self.client.force_login(self.friend_user)
        resp = self.client.get(self.author_commented_single_url(self.friend, self.friend_comment))

        self.assertEqual(resp.status_code, 200)

    def test_author_commented_single_get_comment_not_found(self):
        """Returns 404 for non-existent comment"""
        self.client.force_login(self.owner_user)
        invalid_serial = uuid.uuid4()
        resp = self.client.get(f"/api/authors/{self.owner.serial}/commented/{invalid_serial}/")

        self.assertEqual(resp.status_code, 404)

    def test_author_commented_single_get_wrong_author(self):
        """Returns 404 if comment doesn't belong to the author"""
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.author_commented_single_url(self.owner, self.friend_comment))

        self.assertEqual(resp.status_code, 404)

    def test_author_commented_single_get_embeds_web_url(self):
        """Response includes web URL field"""
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.author_commented_single_url(self.owner, self.owner_comment))
        
        self.assertEqual(resp.status_code, 200)
        expected_web = f"http://testserver/authors/{self.owner.serial}/comments/{self.owner_comment.serial}"
        self.assertEqual(resp.data["web"], expected_web)
        
    # GET /authors/{author_serial}/entries/{entry_serial}/comments/ Tests VVV
    
    def test_entry_comments_get_returns_entry_comments(self):
        """GET returns paginated comments for entry"""
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.entry_comments_url(self.public_entry))
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["type"], "comments")
        self.assertEqual(resp.data["count"], 2)
        
    def test_entry_comments_get_filters_by_visibility(self):
        """Comments are filtered based on viewer permissions"""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.entry_comments_url(self.friends_entry))
        
        self.assertEqual(resp.status_code, 403) # cannot view
        
    def test_entry_comments_get_stranger_sees_public_entry_comments(self):
        """Stranger sees public comments on public entry"""
        self.client.force_login(self.stranger_user)
        resp = self.client.get(self.entry_comments_url(self.public_entry))
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2) # both comments exist
        
    def test_entry_comments_get_friend_sees_friends_entry_comments(self):
        """Friend sees all comments on friends only entry"""
        self.client.force_login(self.friend_user)
        resp = self.client.get(self.entry_comments_url(self.friends_entry))
        
        self.assertEqual(resp.status_code, 200)
        contents = [c["content"] for c in resp.data["src"]]
        self.assertIn("Friends only comment", contents)
        self.assertIn("Former friend comment", contents)
        
    def test_entry_comments_get_former_friend_sees_only_own_comment(self):
        """Former friend sees only their own comment on friends only entry"""
        self.client.force_login(self.former_user)
        resp = self.client.get(self.entry_comments_url(self.friends_entry))
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["src"]), 1)
        self.assertEqual(resp.data["src"][0]["content"], "Former friend comment")
        
    def test_entry_comments_get_owner_sees_all_comments(self):
        """Entry owner sees all comments on their entry"""
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.entry_comments_url(self.friends_entry))
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)
        
    def test_entry_comments_get_unauthenticated_cannot_view_friends_entry(self):
        """Unauthenticated user cannot view comments on friends only entry"""
        resp = self.client.get(self.entry_comments_url(self.friends_entry))
        self.assertEqual(resp.status_code, 403)
        
    def test_entry_comments_get_unauthenticated_can_view_public_entry(self):
        """Unauthenticated user can view comments on public entry"""
        resp = self.client.get(self.entry_comments_url(self.public_entry))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)
        
    def test_entry_comments_get_with_pagination(self):
        """Entry comments GET respects pagination parameters"""
        for i in range(5):
            self.make_comment(self.friend, self.public_entry, f"Comment {i}")
            
        self.client.force_login(self.owner_user)
        resp = self.client.get(f"{self.entry_comments_url(self.public_entry)}?page=1&size=3")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["page_number"], 1)
        self.assertEqual(resp.data["size"], 3)
        self.assertEqual(len(resp.data["src"]), 3)
        
    def test_entry_comments_get_returns_empty_for_entry_with_no_comments(self):
        """Returns empty list for entry with no comments"""
        empty_entry = self.make_entry(self.owner, "Empty entry")
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.entry_comments_url(empty_entry))
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 0)
        self.assertEqual(resp.data["src"], [])
        
    def test_entry_comments_get_requires_entry_to_exist(self):
        """Returns 404 for non-existent entry"""
        self.client.force_login(self.owner_user)
        invalid_serial = uuid.uuid4()
        resp = self.client.get(f"/api/authors/{self.owner.serial}/entries/{invalid_serial}/comments/")
        
        self.assertEqual(resp.status_code, 404)
        
    def test_entry_comments_get_comments_ordered_by_published(self):
        """Comments are ordered by published date descending"""
        self.client.force_login(self.owner_user)
        newer_comment = self.make_comment(self.friend, self.public_entry, "Newer comment")
        newer_comment.published = timezone.now()
        newer_comment.save()
        
        resp = self.client.get(self.entry_comments_url(self.public_entry))
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["src"][0]["content"], "Newer comment")
        
    def test_entry_comments_get_returns_full_comment_payload(self):
        """Each comment includes all expected fields"""
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.entry_comments_url(self.public_entry))
        
        self.assertEqual(resp.status_code, 200)
        comment = resp.data["src"][0]
        self.assertIn("type", comment)
        self.assertIn("author", comment)
        self.assertIn("content", comment)
        self.assertIn("published", comment)
        self.assertIn("id", comment)
        self.assertIn("url", comment)
        
    # edge cases
    
    def test_author_commented_get_invalid_page_returns_empty(self):
        """Invalid page returns empty results"""
        self.client.force_login(self.owner_user)
        resp = self.client.get(f"{self.author_commented_url(self.owner)}?page=999&size=10")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["src"], [])
        
    def test_author_commented_post_handles_missing_content_type(self):
        """POST works without content_type (defaults to text/plain)"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "content": "No content type",
            },
            format="json",
        )
        
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["contentType"], "text/plain")
        
    def test_author_commented_post_handles_content_type_aliases(self):
        """POST accepts contentType or content_type"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "content": "With content_type",
                "content_type": "text/markdown",
            },
            format="json",
        )
        
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["contentType"], "text/markdown")
        
    def test_author_commented_post_handles_empty_string(self):
        """Rejects empty comment text"""
        self.client.force_login(self.friend_user)
        resp = self.client.post(
            self.author_commented_url(self.friend),
            data={
                "type": "comment",
                "entry": self.public_entry.url,
                "content": "",
            },
            format="json",
        )
        
        self.assertEqual(resp.status_code, 400)
        
    def test_author_commented_single_get_unauthenticated_public_comment(self):
        """Unauthenticated user can view public comment"""
        resp = self.client.get(self.author_commented_single_url(self.friend, self.public_comment))
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"], "Public comment")
        
    def test_entry_comments_get_handles_special_characters(self):
        """Handles comments with special characters"""
        special_comment = self.make_comment(
            self.friend, 
            self.public_entry, 
            "Special chars: !@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`"
        )
        self.client.force_login(self.owner_user)
        resp = self.client.get(self.entry_comments_url(self.public_entry))
        
        self.assertEqual(resp.status_code, 200)
        contents = [c["content"] for c in resp.data["src"]]
        self.assertIn(special_comment.content, contents)