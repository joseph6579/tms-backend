from django_filters import FilterSet, BooleanFilter
from dispatch.models import TripStop


class TripStopFilter(FilterSet):
    """
    Add filter to get stops with orders
    """

    without_order = BooleanFilter(field_name='order_id', lookup_expr='isnull', label='Without Order')
    without_driver = BooleanFilter(field_name='driver_profile_id', lookup_expr='isnull', label='Without Driver')

    class Meta:
        model = TripStop
        fields = {
            'driver_profile__id': ['exact'],
            'trip__id': ['exact'],
            'order__id': ['exact'],
            'stop_type': ['exact', 'in'],
            'completed': ['exact'],
            'completed_by__id': ['exact'],
        }
