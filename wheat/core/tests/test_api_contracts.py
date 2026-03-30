from urllib.parse import quote

from rest_framework.test import APITestCase

from core.tests.assertions import (
    assert_author_shape,
    assert_collection_shape,
    assert_comment_shape,
    assert_entry_shape,
    assert_like_shape,
)
from core.tests.factories import (
    make_comment,
    make_entry,
    make_entry_like,
    make_follow,
    make_local_author,
)


class ApiContractTests(APITestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="contract-owner",
            display_name="Contract Owner",
        )
        self.commenter_user, self.commenter = make_local_author(
            username="contract-commenter",
            display_name="Contract Commenter",
        )
        self.follower_user, self.follower = make_local_author(
            username="contract-follower",
            display_name="Contract Follower",
        )

        self.entry = make_entry(
            author=self.owner,
            title="Contract Entry",
            content="contract body",
            visibility="PUBLIC",
        )
        self.comment = make_comment(
            author=self.commenter,
            entry=self.entry,
            content="contract comment",
        )
        self.like = make_entry_like(
            author=self.commenter,
            entry=self.entry,
        )
        make_follow(actor=self.follower, target=self.owner, status="REQUESTED")

    def test_authors_collection_contract(self):
        response = self.client.get("/api/authors/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        assert_collection_shape(self, data, collection_type="authors", item_key="authors")
        self.assertGreaterEqual(len(data["authors"]), 1)
        assert_author_shape(self, data["authors"][0])

    def test_single_author_contract(self):
        response = self.client.get(f"/api/authors/{self.owner.serial}/")

        self.assertEqual(response.status_code, 200)
        assert_author_shape(self, response.json())

    def test_single_entry_contract(self):
        response = self.client.get(f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        assert_entry_shape(self, data)
        self.assertIn("likes", data)
        assert_collection_shape(self, data["likes"], collection_type="likes")
        self.assertIn("comments", data)
        assert_collection_shape(self, data["comments"], collection_type="comments")
        assert_comment_shape(self, data["comments"]["src"][0])

    def test_entries_collection_contract(self):
        response = self.client.get(f"/api/authors/{self.owner.serial}/entries/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        assert_collection_shape(self, data, collection_type="entries")
        self.assertIn("entries", data)
        self.assertGreaterEqual(len(data["src"]), 1)
        assert_entry_shape(self, data["src"][0])

    def test_single_comment_contract(self):
        response = self.client.get(f"/api/authors/{self.commenter.serial}/commented/{self.comment.serial}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        assert_comment_shape(self, data)
        self.assertIn("likes", data)
        assert_collection_shape(self, data["likes"], collection_type="likes")

    def test_comments_collection_contract(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/comments/"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        assert_collection_shape(self, data, collection_type="comments")
        self.assertGreaterEqual(len(data["src"]), 1)
        assert_comment_shape(self, data["src"][0])

    def test_single_like_contract(self):
        encoded_like = quote(self.like.url, safe="")

        response = self.client.get(f"/api/liked/{encoded_like}/")

        self.assertEqual(response.status_code, 200)
        assert_like_shape(self, response.json())

    def test_likes_collection_contract(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/likes/"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        assert_collection_shape(self, data, collection_type="likes")
        self.assertGreaterEqual(len(data["src"]), 1)
        assert_like_shape(self, data["src"][0])

    def test_follow_request_contract(self):
        self.client.force_login(self.owner_user)

        response = self.client.get(f"/api/authors/{self.owner.serial}/follow_requests")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(response.json()[0]["type"], "follow")
        self.assertIn("summary", response.json()[0])
        assert_author_shape(self, response.json()[0]["actor"])
        assert_author_shape(self, response.json()[0]["object"])
