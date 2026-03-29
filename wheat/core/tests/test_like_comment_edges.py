from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from core.tests.factories import (
    make_comment,
    make_comment_like,
    make_entry,
    make_entry_like,
    make_local_author,
)


class LikeAndCommentEdgeCaseTests(APITestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="like-owner",
            display_name="Like Owner",
        )
        self.liker_user, self.liker = make_local_author(
            username="like-liker",
            display_name="Like Liker",
        )

        self.public_entry = make_entry(
            author=self.owner,
            title="Public Entry",
            content="public body",
            visibility="PUBLIC",
        )
        self.public_comment = make_comment(
            author=self.owner,
            entry=self.public_entry,
            content="public comment",
        )
        self.deleted_entry = make_entry(
            author=self.owner,
            title="Deleted Entry",
            content="deleted body",
            visibility="DELETED",
        )

    def test_unlike_entry_then_relike_restores_like(self):
        self.client.force_login(self.liker_user)

        like_response = self.client.post(
            f"/api/authors/{self.liker.serial}/liked/",
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )
        unlike_response = self.client.post(
            f"/api/authors/{self.liker.serial}/liked/",
            data={"type": "unlike", "object": self.public_entry.url},
            format="json",
        )
        relike_response = self.client.post(
            f"/api/authors/{self.liker.serial}/liked/",
            data={"type": "like", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(like_response.status_code, 201)
        self.assertEqual(unlike_response.status_code, 200)
        self.assertEqual(relike_response.status_code, 201)

        likes_response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/likes/"
        )
        self.assertEqual(likes_response.status_code, 200)
        self.assertEqual(likes_response.json()["count"], 1)

    def test_unlike_comment_then_relike_restores_like(self):
        self.client.force_login(self.liker_user)

        like_response = self.client.post(
            f"/api/authors/{self.liker.serial}/liked/",
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )
        unlike_response = self.client.post(
            f"/api/authors/{self.liker.serial}/liked/",
            data={"type": "unlike", "object": self.public_comment.url},
            format="json",
        )
        relike_response = self.client.post(
            f"/api/authors/{self.liker.serial}/liked/",
            data={"type": "like", "object": self.public_comment.url},
            format="json",
        )

        self.assertEqual(like_response.status_code, 201)
        self.assertEqual(unlike_response.status_code, 200)
        self.assertEqual(relike_response.status_code, 201)

        likes_response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/{self.public_entry.serial}/comments/{self.public_comment.serial}/likes/"
        )
        self.assertEqual(likes_response.status_code, 200)
        self.assertEqual(likes_response.json()["count"], 1)

    def test_unlike_missing_like_returns_not_found(self):
        self.client.force_login(self.liker_user)

        response = self.client.post(
            f"/api/authors/{self.liker.serial}/liked/",
            data={"type": "unlike", "object": self.public_entry.url},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Like not found")

    def test_author_liked_orders_mixed_likes_by_published_desc_with_pagination(self):
        now = timezone.now()
        older_like = make_entry_like(
            author=self.liker,
            entry=self.public_entry,
            published=now - timedelta(hours=1),
        )
        newer_like = make_comment_like(
            author=self.liker,
            comment=self.public_comment,
            published=now,
        )

        self.client.force_login(self.liker_user)
        first_page = self.client.get(f"/api/authors/{self.liker.serial}/liked/?page=1&size=1")
        second_page = self.client.get(f"/api/authors/{self.liker.serial}/liked/?page=2&size=1")

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(first_page.json()["count"], 2)
        self.assertEqual(first_page.json()["src"][0]["id"], newer_like.url)
        self.assertEqual(second_page.json()["src"][0]["id"], older_like.url)

    def test_comment_post_to_deleted_entry_is_rejected(self):
        self.client.force_login(self.liker_user)

        response = self.client.post(
            f"/api/authors/{self.liker.serial}/commented/",
            data={
                "type": "comment",
                "entry": self.deleted_entry.url,
                "content": "should fail",
                "contentType": "text/plain",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"],
            "You don't have permission to comment on this entry",
        )
