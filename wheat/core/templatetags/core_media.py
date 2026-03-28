from django import template

from ..helpers import build_author_profile_image_url, build_browser_entry_image_url


register = template.Library()


@register.simple_tag
def author_avatar_url(author, request=None):
    return build_author_profile_image_url(author, request)


@register.simple_tag
def entry_image_url(entry, request=None):
    return build_browser_entry_image_url(entry, request)
