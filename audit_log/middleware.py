from .utils import reset_audit_context, set_audit_context


class AuditRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user if request.user.is_authenticated else None
        token = set_audit_context(user, request.META.get('REMOTE_ADDR'))
        try:
            return self.get_response(request)
        finally:
            reset_audit_context(token)
