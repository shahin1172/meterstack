import threading

_thread_locals = threading.local()

def get_current_request_id():
    return getattr(_thread_locals, 'request_id', None)

def set_current_request_id(request_id):
    _thread_locals.request_id = request_id