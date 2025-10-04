from django_filters import FilterSet

from dispatch.models import Trip


class TripsFilter(FilterSet):
    class Meta:
        model = Trip
        fields = {
            'organisation__id': ['exact'],
            'driver_profile__id': ['exact', 'in'],
            'vehicle__id': ['exact', 'in'],
            'status': ['exact', 'in'],
            'distance': ['lt', 'lte', 'gt', 'gte', 'exact'],
            'created_at': ['range', 'exact'],
            'updated_at': ['range', 'exact'],
            'completed_time': ['range', 'exact'],
        }


class DriverTripsFilter(FilterSet):
    class Meta:
        model = Trip
        fields = {
            'driver_profile__id': ['exact'],
        }