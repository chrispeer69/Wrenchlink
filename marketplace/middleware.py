from django.conf import settings
from django.http import HttpResponse


class RequestSizeLimitMiddleware:
    """Reject oversized request bodies before Django parses uploaded files."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        content_length = request.META.get("CONTENT_LENGTH")
        if content_length:
            try:
                if int(content_length) > settings.MAX_REQUEST_BODY_SIZE:
                    return HttpResponse(
                        "Request body is too large.", status=413, content_type="text/plain"
                    )
            except ValueError:
                return HttpResponse(
                    "Invalid Content-Length header.", status=400, content_type="text/plain"
                )
        return self.get_response(request)
