from django_filters import FilterSet

from organisations.models import Store


class StoreFilter(FilterSet):
    class Meta:
        model = Store
        fields = {'key': ['exact'], 'organisation__id': ['exact']}
