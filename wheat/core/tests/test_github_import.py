import io
import json
from unittest.mock import patch
from urllib.error import HTTPError

from django.test import TestCase
from django.utils.dateparse import parse_datetime

from core.github import fetch_public_events, normalize_github_username
from core.github_to_entries import event_to_entry_data, save_event_as_entry
from core.models import Entry
from core.tests.factories import make_local_author


class GithubImportTests(TestCase):
    def setUp(self):
        self.author_user, self.author = make_local_author(
            username="github-author",
            display_name="Github Author",
            github="https://github.com/github-author",
        )

    def test_normalize_github_username_accepts_supported_formats(self):
        cases = {
            "torvalds": "torvalds",
            "@torvalds": "torvalds",
            "https://github.com/torvalds": "torvalds",
            "https://github.com/torvalds/linux": "torvalds",
            "github.com/torvalds": "torvalds",
            "www.github.com/torvalds": "torvalds",
            "": None,
            None: None,
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_github_username(raw), expected)

    @patch("core.github.urlopen")
    def test_fetch_public_events_returns_empty_list_for_non_list_json(self, mock_urlopen):
        mock_response = io.BytesIO(json.dumps({"unexpected": True}).encode("utf-8"))
        mock_urlopen.return_value.__enter__.return_value = mock_response

        events = fetch_public_events("https://github.com/example")

        self.assertEqual(events, [])

    @patch("core.github.urlopen")
    def test_fetch_public_events_returns_empty_list_on_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            url="https://api.github.com/users/example/events/public",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        events = fetch_public_events("https://github.com/example")

        self.assertEqual(events, [])

    @patch("core.github.urlopen")
    def test_fetch_public_events_clamps_per_page_to_github_limit(self, mock_urlopen):
        mock_response = io.BytesIO(json.dumps([]).encode("utf-8"))
        mock_urlopen.return_value.__enter__.return_value = mock_response

        fetch_public_events("https://github.com/example", per_page=1000)

        request = mock_urlopen.call_args.args[0]
        self.assertIn("per_page=100", request.full_url)

    def test_event_to_entry_data_handles_push_and_create_events(self):
        push_event = {
            "id": "push-1",
            "type": "PushEvent",
            "created_at": "2026-03-29T12:00:00Z",
            "actor": {"login": "github-author"},
            "repo": {"name": "wheat/project"},
            "payload": {"commits": [{"id": "1"}, {"id": "2"}]},
        }
        create_event = {
            "id": "create-1",
            "type": "CreateEvent",
            "created_at": "2026-03-29T13:00:00Z",
            "actor": {"login": "github-author"},
            "repo": {"name": "wheat/project"},
            "payload": {"ref_type": "branch", "ref": "main"},
        }

        push_data = event_to_entry_data(push_event, self.author)
        create_data = event_to_entry_data(create_event, self.author)

        self.assertIn("pushed 2 commit(s)", push_data["content"])
        self.assertIn("created branch main", create_data["content"])
        self.assertTrue(push_data["url"].endswith("/entries/github-push-1"))
        self.assertTrue(create_data["url"].endswith("/entries/github-create-1"))

    def test_event_to_entry_data_ignores_unsupported_events_and_missing_ids(self):
        unsupported = {
            "id": "issue-1",
            "type": "IssuesEvent",
            "created_at": "2026-03-29T12:00:00Z",
        }
        missing_id = {
            "type": "PushEvent",
            "created_at": "2026-03-29T12:00:00Z",
        }

        self.assertIsNone(event_to_entry_data(unsupported, self.author))
        self.assertIsNone(event_to_entry_data(missing_id, self.author))

    def test_save_event_as_entry_is_idempotent_and_updates_existing_row(self):
        first_event = {
            "id": "push-42",
            "type": "PushEvent",
            "created_at": "2026-03-29T10:00:00Z",
            "actor": {"login": "github-author"},
            "repo": {"name": "wheat/project"},
            "payload": {"commits": [{"id": "1"}]},
        }
        updated_event = {
            **first_event,
            "payload": {"commits": [{"id": "1"}, {"id": "2"}, {"id": "3"}]},
        }

        first_entry = save_event_as_entry(first_event, self.author)
        second_entry = save_event_as_entry(updated_event, self.author)

        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(first_entry.pk, second_entry.pk)
        self.assertIn("pushed 3 commit(s)", second_entry.content)
        self.assertEqual(second_entry.published, parse_datetime("2026-03-29T10:00:00Z"))
