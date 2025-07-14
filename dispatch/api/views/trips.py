from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from dispatch.models import Trip, Order, TripStop
from dispatch.services.trip_service import TripService
from dispatch.utils import get_or_create_location
from fleet.models import Vehicle, DriverProfile
from dispatch.api.serializers.trips import TripSerializer, TripCreationSerializer, BasicTripCreationSerializer
from users.models import Driver


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


class TripManagementViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripCreationSerializer

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
        """
        1. Lock all order rows
        2. Create trip
        3. Create trip steps
        4. Update order status to assigned
        5. Update driver profile status to busy
        6. Unlock rows
        """
        data = serializer.validated_data
        driver_profile_id = serializer.data.get('driver_profile', None)
        driver_profile = (
            DriverProfile.objects.only('id', 'vehicle_id').get(id=driver_profile_id) if driver_profile_id else None
        )
        org = self.request.user.organisation
        vehicle = driver_profile.vehicle if driver_profile else None
        trip_status = 'assigned' if driver_profile else 'pending'
        start_location_data = data.get('start_location', None)
        end_location_data = data.get('end_location', None)
        start_location = get_or_create_location(organisation_id=org.id, **start_location_data)
        end_location = (
            get_or_create_location(organisation_id=org.id, **end_location_data) if end_location_data else None
        )

        trip = Trip.objects.create(
            driver_profile=driver_profile,
            vehicle=vehicle,
            organisation=org,
            status=trip_status,
            start_location=start_location,
            end_location=end_location,
        )

        return Response({'detail': 'Trip created successfully'}, status=status.HTTP_201_CREATED)
