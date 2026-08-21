import contextvars
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

_current_tenant = contextvars.ContextVar('current_tenant', default=None)

def get_current_tenant():
    return _current_tenant.get()

def set_current_tenant(tenant):
    _current_tenant.set(tenant)

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # In a real app, resolve tenant from request.user, headers, or domain
        # Example placeholder:
        # if request.user.is_authenticated and hasattr(request.user, 'tenant'):
        #     set_current_tenant(request.user.tenant)
        pass
