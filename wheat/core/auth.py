from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import base64
import threading

from .models import RemoteNode

_thread_local = threading.local()

def require_auth_for_view(require=True):
    """declares that a given view should require authentication. call at the top of views that need auth"""
    _thread_local.require_auth = require

def add_auth_headers(headers, remote):
    """adds basic auth headers to a request for a remote node"""

    if remote and remote.username and remote.password:
        auth_string = f"{remote.username}:{remote.password}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        headers['Authorization'] = f'Basic {encoded_auth}'
    return headers


def get_remote_node_from_request(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Basic "):
        return None
    try:
        encoded = auth_header[6:]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return None

    return RemoteNode.objects.filter(username=username, password=password, is_active=True).first()


def is_remote_node_authenticated(request):
    return get_remote_node_from_request(request) is not None


def is_local_author_authenticated(request, author):
    return (
        request.user.is_authenticated
        and hasattr(request.user, "author_profile")
        and request.user.author_profile == author
    )


class AuthMiddleware(MiddlewareMixin):
    """middleware requiring basic auth for API calls"""

    def process_request(self, request):
        if hasattr(_thread_local, 'require_auth'):
            delattr(_thread_local, 'require_auth')
        return None

    def process_response(self, request, response):

        if getattr(_thread_local, 'require_auth', False) and response.status_code==200 and not request.user.is_authenticated:
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if not auth_header:
                return HttpResponse('Authentication required', status=401, headers={'WWW-Authenticate': 'Basic realm="Node to Node API"'})

            if auth_header.startswith('Basic '):
                try:
                    encoded = auth_header[6:]
                    decoded = base64.b64decode(encoded).decode('utf-8')
                    username, password = decoded.split(':', 1)

                    try:
                        remote_node = RemoteNode.objects.get(username=username, password=password, is_active=True)
                        request.is_remote_node = True
                        request.remote_node = remote_node
                        request.remote_node_name = remote_node.name or remote_node.base_url
                        return response

                    except RemoteNode.DoesNotExist:
                        return HttpResponse('Invalid credentials',status=401,headers={'WWW-Authenticate': 'Basic realm="Node to Node API"'})

                except (ValueError, UnicodeDecodeError):
                    return HttpResponse('Invalid auth header format', status=400)

        return response