import urllib.parse

from rest_framework.test import APITestCase

from core.models import Follow
from core.tests.factories import make_local_author


class FollowStateMachineTests(APITestCase):
    def setUp(self):
        self.actor_user, self.actor = make_local_author(
            username="fsm-actor",
            display_name="FSM Actor",
        )
        self.target_user, self.target = make_local_author(
            username="fsm-target",
            display_name="FSM Target",
        )
        self.other_user, self.other = make_local_author(
            username="fsm-other",
            display_name="FSM Other",
        )

        self.encoded_target = urllib.parse.quote(self.target.url, safe="")
        self.encoded_actor = urllib.parse.quote(self.actor.url, safe="")
        self.encoded_other = urllib.parse.quote(self.other.url, safe="")

    def test_following_put_re_requests_rejected_follow_via_api(self):
        follow = Follow.objects.create(actor=self.actor, target=self.target, status="REJECTED")
        self.client.force_login(self.actor_user)

        response = self.client.put(
            f"/api/authors/{self.actor.serial}/following/{self.encoded_target}"
        )

        self.assertEqual(response.status_code, 204)
        follow.refresh_from_db()
        self.assertEqual(follow.status, "REQUESTED")

    def test_following_put_on_accepted_follow_keeps_status_accepted(self):
        follow = Follow.objects.create(actor=self.actor, target=self.target, status="ACCEPTED")
        self.client.force_login(self.actor_user)

        response = self.client.put(
            f"/api/authors/{self.actor.serial}/following/{self.encoded_target}"
        )

        self.assertEqual(response.status_code, 204)
        follow.refresh_from_db()
        self.assertEqual(follow.status, "ACCEPTED")

    def test_following_delete_then_put_allows_refollow(self):
        Follow.objects.create(actor=self.actor, target=self.target, status="REQUESTED")
        self.client.force_login(self.actor_user)

        delete_response = self.client.delete(
            f"/api/authors/{self.actor.serial}/following/{self.encoded_target}"
        )
        put_response = self.client.put(
            f"/api/authors/{self.actor.serial}/following/{self.encoded_target}"
        )

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(put_response.status_code, 204)
        follow = Follow.objects.get(actor=self.actor, target=self.target)
        self.assertEqual(follow.status, "REQUESTED")

    def test_friendship_breaks_immediately_when_one_side_unfollows(self):
        Follow.objects.create(actor=self.actor, target=self.target, status="ACCEPTED")
        Follow.objects.create(actor=self.target, target=self.actor, status="ACCEPTED")
        self.client.force_login(self.actor_user)

        response = self.client.delete(
            f"/api/authors/{self.actor.serial}/following/{self.encoded_target}"
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.actor.get_friends().filter(pk=self.target.pk).exists())
        self.assertFalse(self.target.get_friends().filter(pk=self.actor.pk).exists())

    def test_follower_put_on_already_accepted_follow_returns_not_found_current_behavior(self):
        Follow.objects.create(actor=self.other, target=self.target, status="ACCEPTED")
        self.client.force_login(self.target_user)

        response = self.client.put(
            f"/api/authors/{self.target.serial}/followers/{self.encoded_other}"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Follow request not found.")

    def test_follower_delete_revokes_accepted_follow_and_friendship(self):
        Follow.objects.create(actor=self.actor, target=self.target, status="ACCEPTED")
        Follow.objects.create(actor=self.target, target=self.actor, status="ACCEPTED")
        self.client.force_login(self.target_user)

        response = self.client.delete(
            f"/api/authors/{self.target.serial}/followers/{self.encoded_actor}"
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Follow.objects.filter(actor=self.actor, target=self.target).exists())
        self.assertFalse(self.actor.get_friends().filter(pk=self.target.pk).exists())
        self.assertFalse(self.target.get_friends().filter(pk=self.actor.pk).exists())
