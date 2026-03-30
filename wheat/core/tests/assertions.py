def assert_author_shape(testcase, data):
    testcase.assertEqual(data["type"], "author")
    for key in ("id", "host", "displayName", "github", "profileImage", "web"):
        testcase.assertIn(key, data)


def assert_entry_shape(testcase, data):
    testcase.assertEqual(data["type"], "entry")
    for key in ("title", "id", "contentType", "content", "author", "published", "visibility"):
        testcase.assertIn(key, data)
    assert_author_shape(testcase, data["author"])


def assert_comment_shape(testcase, data):
    testcase.assertEqual(data["type"], "comment")
    for key in ("id", "author", "contentType", "published", "entry"):
        testcase.assertIn(key, data)
    testcase.assertTrue("comment" in data or "content" in data)
    assert_author_shape(testcase, data["author"])


def assert_like_shape(testcase, data):
    testcase.assertEqual(data["type"], "like")
    for key in ("id", "author", "published", "object"):
        testcase.assertIn(key, data)
    assert_author_shape(testcase, data["author"])


def assert_collection_shape(testcase, data, *, collection_type, item_key=None):
    testcase.assertEqual(data["type"], collection_type)
    for key in ("page_number", "size", "count"):
        testcase.assertIn(key, data)
    if item_key is not None:
        testcase.assertIn(item_key, data)
    else:
        testcase.assertIn("src", data)
