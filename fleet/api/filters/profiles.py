import django_filters

from fleet.models import DriverProfile


class DriverProfileFilter(django_filters.FilterSet):
    has_vehicle = django_filters.BooleanFilter(field_name='vehicle_id', lookup_expr='isnull')

    class Meta:
        model = DriverProfile
        fields = {
            'driver_group_id': ['exact', 'in'],
            'active': ['exact'],
            'status': ['exact'],
            'vehicle_id': ['exact', 'in'],
        }
