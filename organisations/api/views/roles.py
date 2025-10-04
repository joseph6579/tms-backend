from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from organisations.models import Role, Permission
from organisations.api.serializers.roles import RoleSerializer, PermissionSerializer
from organisations.permissions import IsOrganisationAdmin


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsOrganisationAdmin]

    def get_queryset(self):
        return Role.objects.filter(organisation=self.request.user.organisation)

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])

        permissions = Permission.objects.filter(id__in=permission_ids, organisation=request.user.organisation)

        role.permissions.set(permissions)
        return Response({'status': 'permissions assigned'})


class PermissionViewSet(viewsets.ModelViewSet):
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsOrganisationAdmin]

    def get_queryset(self):
        return Permission.objects.filter(organisation=self.request.user.organisation)
