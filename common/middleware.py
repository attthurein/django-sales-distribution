"""
Middleware to set current user in thread-local for audit logging.
"""
from .audit import set_current_user


class AuditMiddleware:
    """Store current user so audit signals can access it."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        set_current_user(user if (user and user.is_authenticated) else None)
        response = self.get_response(request)
        set_current_user(None)  # Clear after request
        return response
