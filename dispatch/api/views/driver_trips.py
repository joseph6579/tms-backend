from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django_filters import rest_framework as django_filters

from commons.constants import TripStatusChoices
from dispatch.api.filters.trips import DriverTripsFilter
from dispatch.api.serializers.driver_trips import DriverTripListSerializer
from dispatch.models import Trip, TripStop, Order
from dispatch.services.driver_trips import driver_trips_svc


class DriverTripViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DriverTripListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = DriverTripsFilter

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)
        # if role != 'driver':
        #     return Trip.objects.none()

        # trip stop fields
        trip_stop_fields = driver_trips_svc.trip_stop_fields()
        trip_stop_prefetch = Prefetch('stops', queryset=TripStop.objects.only(*trip_stop_fields))

        # order related fields
        order_related_fields = driver_trips_svc.order_related_fields()
        order_fields = driver_trips_svc.order_fields()
        orders_prefetch = Prefetch(
            'orders', queryset=Order.objects.select_related(*order_related_fields).only(*order_fields)
        )

        # Trip related fields
        triple_related_fields = driver_trips_svc.trip_related_fields()
        # Trip fields to fetch
        trip_fields = driver_trips_svc.trip_fields()
        incomplete_trip_statuses = TripStatusChoices.incomplete_statuses()
        qs = (
            Trip.objects.only(*trip_fields)
            .select_related(*triple_related_fields)
            .prefetch_related(trip_stop_prefetch, orders_prefetch)
            .filter(status__in=incomplete_trip_statuses)
        )
        return qs
