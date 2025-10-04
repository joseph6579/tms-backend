from rest_framework import serializers
from organisations.models import Role, Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'description']
        read_only_fields = ['organisation']

    def create(self, validated_data):
        validated_data['organisation'] = self.context['request'].user.organisation
        return super().create(validated_data)


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=False)

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'is_active']
        read_only_fields = ['organisation']

    def create(self, validated_data):
        permissions_data = validated_data.pop('permissions', [])
        validated_data['organisation'] = self.context['request'].user.organisation
        role = super().create(validated_data)

        # Add permissions
        for perm_data in permissions_data:
            permission = Permission.objects.create(organisation=role.organisation, **perm_data)
            role.permissions.add(permission)

        return role

    def update(self, instance, validated_data):
        permissions_data = validated_data.pop('permissions', [])
        role = super().update(instance, validated_data)

        # Update permissions
        role.permissions.clear()
        for perm_data in permissions_data:
            permission = Permission.objects.create(organisation=role.organisation, **perm_data)
            role.permissions.add(permission)

        return role
