from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from ..auth import require_auth_for_view
from ..helpers import fetch_remote_image, resolve_image_proxy_target


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def image_proxy(request):
    require_auth_for_view(False)
    target = resolve_image_proxy_target(request.GET.get("url"), request)

    if target.get("kind") == "local":
        return HttpResponseRedirect(target["path"])

    if target.get("kind") == "remote":
        fetched = fetch_remote_image(target["url"], target["remote_node"])
        if fetched["status"] != 200:
            return Response({"error": fetched["error"]}, status=fetched["status"])
        return HttpResponse(fetched["content"], content_type=fetched["content_type"])

    return Response({"error": target["error"]}, status=target["status"])
