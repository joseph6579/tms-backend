from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsMasterUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_master_user
    
class IsMasterUserorReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_master_user or request.method in SAFE_METHODS