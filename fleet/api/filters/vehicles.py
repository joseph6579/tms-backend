from django.db.models import Exists, OuterRef
import django_filters

from fleet.models import Vehicle, DriverProfile


class VehicleFilter(django_filters.FilterSet):
    assigned = django_filters.BooleanFilter(method='filter_assigned')

    class Meta:
        model = Vehicle
        fields = {'driver_profile__id': ['exact', 'in']}

    def filter_assigned(self, queryset, name, value):
        profile_qs = DriverProfile.objects.filter(
            vehicle_id=OuterRef('pk'),
            organisation_id=OuterRef('organisation_id'),  # critical: ensures same organisation
        )
        return queryset.annotate(has_profile=Exists(profile_qs)).filter(has_profile=value)
