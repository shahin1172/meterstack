# core/middleware.py
import uuid
import logging
import logging
from .local import get_current_request_id

logger = logging.getLogger(__name__)

# core/middleware.py (updated)
import uuid
from .local import set_current_request_id

class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id
        set_current_request_id(request_id)
        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response



class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_current_request_id()
        return True