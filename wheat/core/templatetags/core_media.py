import json
import urllib.parse

from django import template

from ..helpers import (
    build_author_profile_image_url,
    build_browser_entry_image_url,
    build_local_avatar_placeholder_url,
    build_media_proxy_url,
    is_allowlisted_media_url,
    is_same_node_media_url,
    normalize_url,
)
from ..models import RemoteNode


register = template.Library()


@register.simple_tag
def author_avatar_url(author, request=None):
    return build_author_profile_image_url(author, request)


@register.simple_tag
def entry_image_url(entry, request=None):
    return build_browser_entry_image_url(entry, request)


@register.simple_tag
def browser_media_url(media_url, request=None, fallback_url=None):
    raw = (media_url or "").strip()
    fallback = fallback_url or build_local_avatar_placeholder_url(request)
    if not raw:
        return fallback
    if is_same_node_media_url(raw, request):
        return raw
    if is_allowlisted_media_url(raw, request):
        return build_media_proxy_url(raw, request)
    return fallback


@register.simple_tag
def allowlisted_media_origins_json():
    origins = []
    for node in RemoteNode.objects.filter(is_active=True).order_by("base_url", "api_base_url"):
        for candidate in (node.base_url, node.api_base_url):
            parsed = urllib.parse.urlparse((candidate or "").strip())
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                continue
            origin = normalize_url(f"{parsed.scheme}://{parsed.netloc}")
            if origin not in origins:
                origins.append(origin)
    return json.dumps(origins)
