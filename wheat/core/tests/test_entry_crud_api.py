from rest_framework.test import APITestCase

from core.models import Entry
from core.tests.assertions import assert_entry_shape
from core.tests.factories import make_entry, make_local_author


class EntryCrudApiTests(APITestCase):
    def setUp(self):
        self.owner_user, self.owner = make_local_author(
            username="entry-owner",
            display_name="Entry Owner",
        )
        self.other_user, self.other_author = make_local_author(
            username="entry-other",
            display_name="Entry Other",
        )
        self.entry = make_entry(
            author=self.owner,
            title="Original Title",
            content="Original content",
            content_type="text/plain",
            visibility="PUBLIC",
        )

    def test_create_plain_text_entry_via_api(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "title": "Plain Entry",
                "content": "plain body",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        assert_entry_shape(self, data)
        self.assertEqual(data["title"], "Plain Entry")
        self.assertEqual(data["content"], "plain body")
        self.assertEqual(data["contentType"], "text/plain")

    def test_create_markdown_entry_via_api(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "title": "Markdown Entry",
                "content": "# heading",
                "contentType": "text/markdown",
                "visibility": "UNLISTED",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        assert_entry_shape(self, data)
        self.assertEqual(data["contentType"], "text/markdown")
        self.assertEqual(data["visibility"], "UNLISTED")

    def test_create_image_entry_requires_image_url(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "title": "Image Entry",
                "content": "",
                "contentType": "image",
                "visibility": "PUBLIC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "imageUrl is required for image entries")

    def test_create_image_entry_with_image_url(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "title": "Image Entry",
                "content": "",
                "contentType": "image",
                "imageUrl": "https://cdn.example.com/example.png",
                "visibility": "PUBLIC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        assert_entry_shape(self, data)
        self.assertTrue(data["imageUrl"].endswith("/image/"))
        self.assertIn(f"/api/authors/{self.owner.serial}/entries/", data["imageUrl"])
        created = Entry.objects.get(url=data["id"])
        self.assertEqual(created.image_url, "https://cdn.example.com/example.png")

    def test_create_entry_requires_authenticated_owner(self):
        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "title": "No Auth",
                "content": "body",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_create_entry_forbids_non_owner(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "title": "Other User Entry",
                "content": "body",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_put_single_entry_updates_supported_fields(self):
        self.client.force_login(self.owner_user)

        response = self.client.put(
            f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/",
            data={
                "title": "Updated Title",
                "content": "Updated content",
                "contentType": "text/markdown",
                "visibility": "FRIENDS",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, "Updated Title")
        self.assertEqual(self.entry.content, "Updated content")
        self.assertEqual(self.entry.content_type, "text/markdown")
        self.assertEqual(self.entry.visibility, "FRIENDS")

    def test_put_single_entry_forbids_non_owner(self):
        self.client.force_login(self.other_user)

        response = self.client.put(
            f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/",
            data={"title": "Forbidden Update"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_single_entry_soft_deletes_entry(self):
        self.client.force_login(self.owner_user)

        response = self.client.delete(
            f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/"
        )

        self.assertEqual(response.status_code, 204)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.visibility, "DELETED")

    def test_delete_single_entry_forbids_non_owner(self):
        self.client.force_login(self.other_user)

        response = self.client.delete(
            f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/"
        )

        self.assertEqual(response.status_code, 403)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.visibility, "PUBLIC")

    def test_create_entry_defaults_invalid_visibility_to_public(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "title": "Invalid Visibility",
                "content": "body",
                "contentType": "text/plain",
                "visibility": "SUPER-PRIVATE",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["visibility"], "PUBLIC")

    def test_put_image_entry_without_image_url_is_rejected(self):
        image_entry = make_entry(
            author=self.owner,
            title="Image Entry",
            content="",
            content_type="image",
            image_url="https://cdn.example.com/image.png",
            visibility="PUBLIC",
        )
        self.client.force_login(self.owner_user)

        response = self.client.put(
            f"/api/authors/{self.owner.serial}/entries/{image_entry.serial}/",
            data={
                "title": "Broken Image Entry",
                "contentType": "image",
                "imageUrl": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "imageUrl is required for image entries")
        image_entry.refresh_from_db()
        self.assertEqual(image_entry.image_url, "https://cdn.example.com/image.png")

    def test_put_entry_requires_authentication(self):
        response = self.client.put(
            f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/",
            data={"title": "No Auth Update"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_delete_entry_requires_authentication(self):
        response = self.client.delete(
            f"/api/authors/{self.owner.serial}/entries/{self.entry.serial}/"
        )

        self.assertEqual(response.status_code, 401)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.visibility, "PUBLIC")

    def test_create_entry_without_title_uses_default_title(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            f"/api/authors/{self.owner.serial}/entries/",
            data={
                "content": "body only",
                "contentType": "text/plain",
                "visibility": "PUBLIC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        created = Entry.objects.get(url=response.json()["id"])
        self.assertEqual(created.title, "Untitled")
