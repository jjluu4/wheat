import uuid

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from core.models import Author, Entry, Follow, RemoteNode


class PendingFormTemplateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dup-user", password="pass12345")
        self.author = Author.objects.create(
            user=self.user,
            displayName="Dup User",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
            host="http://testserver/api/",
            web=f"http://testserver/authors/{uuid.uuid4()}/",
        )
        self.requester_user = User.objects.create_user(username="dup-requester", password="pass12345")
        self.requester = Author.objects.create(
            user=self.requester_user,
            displayName="Dup Requester",
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{uuid.uuid4()}",
            host="http://testserver/api/",
            web=f"http://testserver/authors/{uuid.uuid4()}/",
        )
        self.entry = Entry.objects.create(
            author=self.author,
            serial=uuid.uuid4(),
            url=f"http://testserver/api/authors/{self.author.serial}/entries/{uuid.uuid4()}",
            title="Pending Entry",
            content="Pending body",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        Follow.objects.create(actor=self.requester, target=self.author, status="REQUESTED")

        self.staff_user = User.objects.create_user(
            username="dup-staff",
            password="pass12345",
            is_staff=True,
        )
        RemoteNode.objects.create(
            name="Pending Remote",
            base_url="http://pending-remote.example.com",
            api_base_url="http://pending-remote.example.com/api",
            username="pending-user",
            password="pending-pass",
            is_active=True,
        )

    def test_signup_page_uses_pending_form_and_helper_script(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "js/pending-actions.js")
        self.assertContains(response, "data-pending-form")

    def test_author_edit_page_uses_pending_form(self):
        self.client.force_login(self.user)

        response = self.client.get(f"/authors/{self.author.serial}/edit/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-pending-form")

    def test_entry_create_page_uses_pending_form(self):
        self.client.force_login(self.user)

        response = self.client.get(f"/authors/{self.author.serial}/entries/new/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-pending-form")

    def test_entry_delete_confirm_page_uses_pending_form(self):
        self.client.force_login(self.user)

        response = self.client.get(f"/authors/{self.author.serial}/entries/{self.entry.serial}/delete/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-pending-form")

    def test_author_profile_follow_controls_render_as_post_forms(self):
        self.client.force_login(self.requester_user)

        response = self.client.get(f"/authors/{self.author.serial}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'method="post"')
        self.assertContains(response, "Cancel request")
        self.assertContains(response, "data-pending-form")
        self.assertNotContains(response, f'href="/authors/{self.author.serial}/follow/"')

    def test_follow_requests_page_uses_pending_forms_for_actions(self):
        self.client.force_login(self.user)

        response = self.client.get(f"/authors/{self.author.serial}/requests/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-pending-form", count=3)

    def test_remote_node_pages_use_pending_forms(self):
        self.client.force_login(self.staff_user)
        node = RemoteNode.objects.get(base_url="http://pending-remote.example.com")

        list_response = self.client.get("/staff/nodes/")
        add_response = self.client.get("/staff/nodes/add/")
        delete_response = self.client.get(f"/staff/nodes/{node.pk}/delete/")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(add_response.status_code, 200)
        self.assertEqual(delete_response.status_code, 200)
        self.assertContains(list_response, "data-pending-form")
        self.assertContains(add_response, "data-pending-form")
        self.assertContains(delete_response, "data-pending-form")

    def test_entry_fragment_comment_form_uses_pending_form_hook(self):
        self.client.force_login(self.user)

        response = self.client.get(f"/authors/{self.author.serial}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'onsubmit="submitComment(event)"')
        self.assertContains(response, "data-pending-form")
