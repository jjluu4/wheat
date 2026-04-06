from core.models import Follow


def follow_request_count(request):
    if not request.user.is_authenticated:
        return {}
    author = getattr(request.user, "author_profile", None)
    if author is None:
        return {}
    count = Follow.objects.filter(target=author, status="REQUESTED").count()
    return {"pending_follow_request_count": count}
