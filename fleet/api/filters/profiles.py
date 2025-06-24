import django_filters

from fleet.models import DriverProfile


class DriverProfileFilter(django_filters.FilterSet):
    class Meta:
        model = DriverProfile
        fields = {
            'driver_group_id': ['exact', 'in'],
            'active': ['exact'],
            'status': ['exact'],
            'vehicle_id': ['exact', 'in'],
        }
