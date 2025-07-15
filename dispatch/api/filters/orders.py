from django_filters import FilterSet

from dispatch.models import Order


class OrderFilter(FilterSet):
    class Meta:
        model = Order
        fields = {
            'created_at': ['exact', 'range'],
            'updated_at': ['exact', 'range'],
            'date_delivered': ['exact', 'range'],
            'date_cancelled': ['exact', 'range'],
            'status': ['exact', 'in'],
            'driver_profile__id': ['exact', 'in'],
            'recipient__id': ['exact', 'in'],
            'buyer__id': ['exact', 'in'],
            'organisation__id': ['exact', 'in'],
            'store__id': ['exact', 'in'],
            'added_by_user__id': ['exact', 'in'],
        }
