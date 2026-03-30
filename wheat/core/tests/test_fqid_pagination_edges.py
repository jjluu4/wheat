from urllib.parse import quote

from rest_framework.test import APITestCase

from core.tests.factories import make_comment, make_entry, make_local_author


class FqidAndPaginationEdgeTests(APITestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="fqid-edge-owner",
            display_name="FQID Edge Owner",
        )
        self.liker_user, self.liker = make_local_author(
            username="fqid-edge-liker",
            display_name="FQID Edge Liker",
        )
        self.entry = make_entry(
            author=self.owner,
            title="FQID Entry",
            content="fqid entry body",
            url=f"http://testserver/api/authors/{self.owner.serial}/entries/fqid-entry/",
        )
        self.comment = make_comment(
            author=self.owner,
            entry=self.entry,
            content="fqid comment body",
            url=f"http://testserver/api/authors/{self.owner.serial}/commented/fqid-comment/",
        )

    def test_entry_fqid_route_matches_trailing_slash_variant(self):
        encoded = quote(self.entry.url.rstrip("/"), safe="")

        response = self.client.get(f"/api/entries/{encoded}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.entry.url)

    def test_comment_fqid_route_matches_trailing_slash_variant(self):
        encoded = quote(self.comment.url.rstrip("/"), safe="")

        response = self.client.get(f"/api/commented/{encoded}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.comment.url)

    def test_like_fqid_route_matches_trailing_slash_variant(self):
        self.client.force_login(self.liker_user)
        like_response = self.client.post(
            f"/api/authors/{self.liker.serial}/liked/",
            data={"type": "like", "object": self.entry.url},
            format="json",
        )
        self.assertEqual(like_response.status_code, 201)

        encoded = quote(like_response.json()["id"].rstrip("/"), safe="")
        response = self.client.get(f"/api/liked/{encoded}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["object"], self.entry.url)

    def test_author_entries_pagination_normalizes_zero_and_negative_values(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/?page=0&size=-2"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["page_number"], 1)
        self.assertEqual(response.json()["size"], 5)

    def test_author_entries_pagination_normalizes_non_integer_values(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/?page=abc&size=def"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["page_number"], 1)
        self.assertEqual(response.json()["size"], 5)

    def test_author_entries_pagination_returns_empty_src_for_large_page_number(self):
        response = self.client.get(
            f"/api/authors/{self.owner.serial}/entries/?page=999&size=5"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["src"], [])
