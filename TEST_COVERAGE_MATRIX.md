# Test Coverage Matrix

This matrix maps major CMPUT 404 user-story areas to the primary automated tests in this repo.
It is a walkthrough aid, not an exhaustive test index.

## Identity And Authors

| Story / Behavior | Primary Tests |
| --- | --- |
| Local author listing and profile shape | `wheat/core/tests/test_authors.py`, `wheat/core/tests/test_api_contracts.py` |
| Signup stays pending until approval | `wheat/core/tests/test_author_auth.py`, `wheat/core/tests/test_admin.py` |
| Admin approval creates author exactly once | `wheat/core/tests/test_admin.py`, `wheat/core/tests/test_remote_node_admin_edges.py` |
| Missing `author_profile` recovery for logged-in users | `wheat/core/tests/test_author_auth.py` |
| Author update auth and owner checks | `wheat/core/tests/test_authors.py`, `wheat/core/tests/test_auth_boundaries.py` |

## Entries And Visibility

| Story / Behavior | Primary Tests |
| --- | --- |
| Entry create/edit/delete API flows | `wheat/core/tests/test_entry_crud_api.py` |
| Public, unlisted, friends-only, deleted direct access | `wheat/core/tests/test_entry_visibility_api.py`, `wheat/core/tests/test_link_visibility.py`, `wheat/core/tests/test_entries.py` |
| Visibility transitions take effect immediately | `wheat/core/tests/test_entry_visibility_api.py` |
| Remote-backed image entries and browser-safe image URLs | `wheat/core/tests/test_entries.py`, `wheat/core/tests/test_media.py` |

## Stream And Profile

| Story / Behavior | Primary Tests |
| --- | --- |
| Stream includes correct local and remote entries | `wheat/core/tests/test_stream_profile_visibility.py` |
| Stream ordering and deleted-entry exclusion | `wheat/core/tests/test_stream_profile_visibility.py`, `wheat/core/tests/tests.py` |
| Profile visibility for anonymous, follower, friend, owner, staff | `wheat/core/tests/test_stream_profile_visibility.py`, `wheat/core/tests/tests.py` |

## Comments And Likes

| Story / Behavior | Primary Tests |
| --- | --- |
| Comment CRUD, visibility, pagination, ordering | `wheat/core/tests/test_comments.py`, `wheat/core/tests/test_remote_comments.py` |
| Like entry/comment happy paths and visibility boundaries | `wheat/core/tests/test_likes.py` |
| Unlike, re-like, missing-like, liked ordering | `wheat/core/tests/test_like_comment_edges.py` |
| Deleted-entry comment rejection | `wheat/core/tests/test_like_comment_edges.py` |

## Following And Friendship

| Story / Behavior | Primary Tests |
| --- | --- |
| Following, followers, follow requests API coverage | `wheat/core/tests/test_following.py` |
| Re-request, refollow, accepted-state behavior, friendship break | `wheat/core/tests/test_follow_state_machine.py` |
| Friends-only visibility after friendship changes | `wheat/core/tests/test_stream_profile_visibility.py`, `wheat/core/tests/test_follow_state_machine.py` |

## Inbox And Federation

| Story / Behavior | Primary Tests |
| --- | --- |
| Inbox auth and remote-node validation | `wheat/core/tests/test_inbox_auth.py` |
| Inbox happy paths for entry, comment, like, follow, accept, unfollow, unlike | `wheat/core/tests/test_inbox.py` |
| Malformed payloads and unsupported object types | `wheat/core/tests/test_inbox_malformed.py` |
| Inbox idempotency and event ordering | `wheat/core/tests/test_inbox_idempotency_ordering.py`, `wheat/core/tests/test_inbox.py` |
| Distribution to remote recipients | `wheat/core/tests/test_distribution.py` |

## FQIDs, Pagination, And Contracts

| Story / Behavior | Primary Tests |
| --- | --- |
| Full URL object IDs and trailing-slash normalization | `wheat/core/tests/test_fqid.py`, `wheat/core/tests/test_fqid_pagination_edges.py` |
| Pagination normalization and large-page behavior | `wheat/core/tests/test_fqid_pagination_edges.py`, `wheat/core/tests/test_comments.py`, `wheat/core/tests/test_likes.py` |
| Contract shape for author/entry/comment/like/follow-related responses | `wheat/core/tests/test_api_contracts.py` |

## Remote Nodes, Admin, And GitHub

| Story / Behavior | Primary Tests |
| --- | --- |
| Remote node management views and forms | `wheat/core/tests/test_remote_nodes.py` |
| Remote node author-catalog API errors and inactive-node behavior | `wheat/core/tests/test_remote_node_admin_edges.py` |
| Admin approval edge cases | `wheat/core/tests/test_admin.py`, `wheat/core/tests/test_remote_node_admin_edges.py` |
| GitHub username normalization, event fetching, event-to-entry import | `wheat/core/tests/test_github_import.py`, `wheat/core/tests/tests.py` |

## Auth And Same-Origin Security

| Story / Behavior | Primary Tests |
| --- | --- |
| Local session vs remote Basic auth boundaries | `wheat/core/tests/test_auth_boundaries.py`, `wheat/core/tests/test_inbox_auth.py` |
| Same-origin media allowlist and proxy safety | `wheat/core/tests/test_media.py`, `wheat/core/tests/test_auth_boundaries.py` |
| Markdown same-origin rewriting | `wheat/core/tests/test_media.py` |
