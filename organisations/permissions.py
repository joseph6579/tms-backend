from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated


class IsMasterUser(IsAuthenticated):
    def has_permission(self, request, view):
        perm = super().has_permission(request, view)
        if not perm:
            return False
        return request.user.is_master_user


class IsMasterUserOrReadOnly(IsAuthenticated):
    def has_permission(self, request, view):
        perm = super().has_permission(request, view)
        if not perm:
            return False
        return request.user.is_master_user or request.method in SAFE_METHODS


class IsOrganisationAdmin(BasePermission):
    """
    Custom permission to only allow organization admins to access the view.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_master_user or request.user.role == 'admin')


class HasOrganisationPermission(BasePermission):
    """
    Custom permission to check if user has specific organization permission.
    """

    def __init__(self, required_permission):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_organisation_permission(self.required_permission)
