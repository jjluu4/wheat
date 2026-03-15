def get_requesting_author(request):
    if request.user.is_authenticated and hasattr(request.user, "author_profile"):
        return request.user.author_profile
    return None


def is_friend(author, requesting_author):
    if not requesting_author:
        return False
    return author.get_friends().filter(serial=requesting_author.serial).exists()


def can_view_entry(entry, requesting_author, user):
    if entry.visibility == "DELETED":
        return user.is_authenticated and user.is_staff

    if entry.visibility in ("PUBLIC", "UNLISTED"):
        return True

    if not user.is_authenticated:
        return False

    if user.is_staff:
        return True

    if requesting_author == entry.author:
        return True

    if entry.visibility == "FRIENDS":
        return is_friend(entry.author, requesting_author)

    return False


def can_view_comment(comment, requesting_author, user):
    entry = comment.entry

    if can_view_entry(entry, requesting_author, user):
        return True

    if entry.visibility == "FRIENDS" and requesting_author == comment.author:
        return True

    return False


def filter_comments_for_viewer(comments_qs, entry, requesting_author, user):
    if entry.visibility == "DELETED":
        if user.is_authenticated and user.is_staff:
            return comments_qs
        return comments_qs.none()

    if can_view_entry(entry, requesting_author, user):
        return comments_qs

    if entry.visibility == "FRIENDS" and requesting_author:
        return comments_qs.filter(author=requesting_author)

    return comments_qs.none()
