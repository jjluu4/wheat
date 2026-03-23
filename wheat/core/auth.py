from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
import base64
import binascii
import threading

from .models import RemoteNode

_thread_local = threading.local()
AUTH_REALM = 'Basic realm="Node to Node API"'


def require_auth_for_view(require=True):
    """Compatibility shim for existing views that annotate auth requirements."""
    _thread_local.require_auth = require


def add_auth_headers(headers, remote):
    """Adds basic auth headers to a request for a remote node."""
    if remote and remote.username and remote.password:
        auth_string = f"{remote.username}:{remote.password}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"
    return headers


def _build_auth_failure_response(message):
    return HttpResponse(message, status=401, headers={"WWW-Authenticate": AUTH_REALM})


def parse_remote_node_auth(request):
    request.is_remote_node = False
    request.remote_node = None
    request.remote_node_name = None
    request.remote_auth_error = None
    request.remote_auth_attempted = False

    auth_header = request.META.get("HTTP_AUTHORIZATION")
    if not auth_header:
        return None

    request.remote_auth_attempted = True

    if not auth_header.startswith("Basic "):
        request.remote_auth_error = "Authentication required"
        return None

    try:
        encoded = auth_header[6:]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError, binascii.Error):
        request.remote_auth_error = "Invalid credentials"
        return None

    try:
        remote_node = RemoteNode.objects.get(username=username, password=password, is_active=True)
    except RemoteNode.DoesNotExist:
        request.remote_auth_error = "Invalid credentials"
        return None

    request.is_remote_node = True
    request.remote_node = remote_node
    request.remote_node_name = remote_node.name or remote_node.base_url
    return remote_node


def get_remote_node_from_request(request):
    remote_node = getattr(request, "remote_node", None)
    if remote_node is not None:
        return remote_node
    return parse_remote_node_auth(request)


def is_remote_node_authenticated(request):
    return get_remote_node_from_request(request) is not None


def is_local_author_authenticated(request, author):
    return (
        request.user.is_authenticated
        and hasattr(request.user, "author_profile")
        and request.user.author_profile == author
    )


def require_remote_node_auth(request):
    if get_remote_node_from_request(request) is not None:
        return None
    return _build_auth_failure_response(
        getattr(request, "remote_auth_error", None) or "Authentication required"
    )


class AuthMiddleware(MiddlewareMixin):
    """Parses remote node basic auth early and exposes the matched remote node on the request."""

    def process_request(self, request):
        if hasattr(_thread_local, "require_auth"):
            delattr(_thread_local, "require_auth")
        parse_remote_node_auth(request)
        return None

    def process_response(self, request, response):
        return response
