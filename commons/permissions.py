from rest_framework.permissions import BasePermission


class HasCompany(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.organisation_id)
