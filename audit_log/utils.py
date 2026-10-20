from contextvars import ContextVar

from .models import ActivityLog


_request_audit_context = ContextVar('request_audit_context', default=(None, None))


def set_audit_context(user, ip_address):
    return _request_audit_context.set((user, ip_address))


def reset_audit_context(token):
    _request_audit_context.reset(token)


def get_audit_context():
    return _request_audit_context.get()


def log_activity(user, action, model_name, object_repr, ip_address=None):
    return ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_repr=str(object_repr)[:255],
        ip_address=ip_address,
    )
