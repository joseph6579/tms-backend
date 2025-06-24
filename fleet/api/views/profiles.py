from rest_framework.viewsets import ReadOnlyModelViewSet

from fleet.api.serializers.profiles import DriverProfileListSerializer
from fleet.models import DriverGroup, DriverProfile


class DriverManagement(ReadOnlyModelViewSet):
    serializer_class = DriverProfileListSerializer

    def get_queryset(self):
        user = self.request.user
        organisation_id = getattr(user, 'organisation_id')
        is_superuser = getattr(user, 'is_superuser')
        related_fields = ['driver', 'vehicle', 'driver_group']
        fields = [
            'id',
            'first_name',
            'last_name',
            'national_id',
            'created_at',
            'status',
            'organisation_id',
            'driver__id',
            'driver__email',
            'driver__is_active',
            'vehicle_id',
            'vehicle__registration_number',
            'driver_group_id',
            'driver_group__name',
        ]
        qs = DriverProfile.objects.select_related(*related_fields).only(*fields)
        if is_superuser:
            return qs.all()
        elif organisation_id:
            return qs.filter(organisation_id=organisation_id).all()
        else:
            qs.none()

    def update_profile(self):
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass

    def mark_as_online(self):
        pass

    def mark_as_offline(self):
        pass
