from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dispatch.api.filters.trips import TripsFilter
from dispatch.api.serializers.trips import TripSerializer, TripListSerializer, BasicTripCreationSerializer
from dispatch.models import Trip, Order, TripStop
from dispatch.services import trip_service
from dispatch.services.trip_service import TripService, trip_svc
from fleet.models import Vehicle
from dispatch.api.serializers.trips import TripSerializer
from organisations.models import Organisation
from dispatch.services.trip_service import TripService, TripBuilder
from fleet.models import Vehicle



class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Trip.objects.filter(orders__organization=self.request.user.organisation).distinct()

    @action(detail=False, methods=['post'])
    def create_from_orders(self, request):
        order_ids = request.data.get('order_ids', [])
        optimize = request.data.get('optimize', False)
        vehicle_id = request.data.get('vehicle_id')
        driver_id = request.data.get('driver_id')

        # Get orders
        orders = Order.objects.filter(id__in=order_ids, organization=request.user.organisation, trip__isnull=True)

        if not orders:
            return Response({'detail': 'No valid orders found'}, status=status.HTTP_400_BAD_REQUEST)

        vehicle = None
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
            except Vehicle.DoesNotExist:
                return Response({'detail': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)

        driver = None
        if driver_id:
            try:
                from users.models import Driver

                driver = Driver.objects.get(id=driver_id)
            except Driver.DoesNotExist:
                return Response({'detail': 'Driver not found'}, status=status.HTTP_404_NOT_FOUND)

        if optimize and request.user.organisation.has_route_optimization:
            # Format data for optimization
            optimization_data = TripService.format_orders_for_optimization(
                orders=orders, vehicles=[vehicle] if vehicle else Vehicle.objects.filter(source='in_house')
            )

            # Call optimization service
            # This is a placeholder - implement actual API call
            optimization_result = []  # Result from optimization service

            # Create trip from optimization result
            trip = TripService.create_trip_from_optimization(
                optimization_result=optimization_result, orders=orders, driver=driver
            )
        else:
            # Create simple trip without optimization
            trip = TripService.create_simple_trip(orders=orders, vehicle=vehicle, driver=driver)

        if not trip:
            return Response({'detail': 'Failed to create trip'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(trip)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def complete_stop(self, request, pk=None):
        trip = self.get_object()
        stop_id = request.data.get('stop_id')

        try:
            stop = TripStop.objects.get(id=stop_id, trip=trip)
        except TripStop.DoesNotExist:
            return Response({'detail': 'Stop not found'}, status=status.HTTP_404_NOT_FOUND)

        stop.status = 'completed'
        stop.completed_at = timezone.now()
        stop.completed_by = request.user
        stop.save()

        # Update order status if this is a delivery stop
        if stop.stop_type == 'drop_off' and stop.order:
            stop.order.status = 'completed'
            stop.order.date_delivered = timezone.now()
            stop.order.save()

        # Check if all stops are completed
        if not trip.stops.exclude(status='completed').exists():
            trip.status = 'completed'
            trip.completed_time = timezone.now()
            trip.save()

        serializer = self.get_serializer(trip)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start_trip(self, request, pk=None):
        trip = self.get_object()

        if trip.status != 'scheduled':
            return Response({'detail': 'Trip cannot be started'}, status=status.HTTP_400_BAD_REQUEST)

        trip.status = 'in_progress'
        trip.actual_start_time = timezone.now()
        trip.save()

        # Update all orders in this trip
        trip.orders.all().update(status='in_progress')

        serializer = self.get_serializer(trip)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete_trip(self, request, pk=None):
        trip = self.get_object()

        if trip.status not in ['in_progress', 'scheduled']:
            return Response({'detail': 'Trip cannot be completed'}, status=status.HTTP_400_BAD_REQUEST)

        trip.status = 'completed'
        trip.completed_time = timezone.now()
        trip.save()

        # Complete all remaining stops
        trip.stops.exclude(status='completed').update(
            status='completed', completed_at=timezone.now(), completed_by=request.user
        )

        # Update all orders in this trip
        trip.orders.all().update(status='completed', date_delivered=timezone.now())

        serializer = self.get_serializer(trip)
        return Response(serializer.data)

      
    @action(detail=False, methods=['get'], url_path='active-steps')
    def active_steps(self, request, *args, **kwargs):
        org = Organisation.objects.first()
        steps = trip_svc.fetch_stops_configuration(org=org)
        return Response(steps)


class TripManagementViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = TripListSerializer
    filterset_class = TripsFilter
    ordering_fields = ['created_at', 'updated_at', 'completed_time', 'estimated_duration', 'distance']

    def get_queryset(self):
        user = self.request.user
        is_superuser = getattr(user, 'is_superuser', False)
        org_id = getattr(user, 'organisation_id', None)

        related_fields = ['driver_profile', 'vehicle', 'start_location', 'end_location']
        fields = [
            'id',
            'created_at',
            'updated_at',
            'status',
            'completed_time',
            'estimated_duration',
            'actual_duration',
            'planned_geometry',
            'actual_geometry',
            'notes',
            'distance',
            'start_location__name',
            'start_location__address',
            'start_location__coordinates',
            'end_location__name',
            'end_location__address',
            'end_location__coordinates',
            'driver_profile_id',
            'driver_profile__first_name',
            'driver_profile__last_name',
            'vehicle_id',
            'vehicle__registration_number',
            'organisation_id',
        ]
        qs = Trip.objects.only(*fields).select_related(*related_fields)
        if is_superuser:
            return qs
        elif org_id:
            return qs.filter(organisation_id=org_id)
        else:
            return qs.none()

    @transaction.atomic()
    @action(methods=['post'], detail=False, url_path='create', serializer_class=BasicTripCreationSerializer)
    def create_trip(self, request, *args, **kwargs):
        """
        Create a trip with a driver
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        org = self.request.user.organisation
        data = serializer.validated_data
        TripBuilder(
            organisation=org,
            driver_profile=data.get('driver_profile'),
            orders_data=data.get('orders'),
            start_loc_data=data.get('start_location'),
            end_loc_data=data.get('end_location'),
        )
        return Response({'detail': 'Trip created successfully'}, status=status.HTTP_201_CREATED)

