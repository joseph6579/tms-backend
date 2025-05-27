from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone

from dispatch.models import Order
from dispatch.api.serializers.orders import OrderSerializer
from dispatch.services.trip_service import TripService

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter orders by user's organization
        return Order.objects.filter(
            organization=self.request.user.organisation,
            is_active=True
        ).select_related(
            'pickup', 'drop_off', 'recipient', 'buyer', 'driver'
        )
    
    def destroy(self, request, *args, **kwargs):
        # Instead of deleting, mark as inactive
        order = self.get_object()
        order.is_active = False
        order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = 'cancelled'
        order.date_cancelled = timezone.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        order.status = 'completed'
        order.date_delivered = timezone.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        order = self.get_object()
        driver_id = request.data.get('driver_id')
        
        if not driver_id:
            return Response(
                {'detail': 'Driver ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from users.models import Driver
            driver = Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            return Response(
                {'detail': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if driver belongs to the same organization
        if driver.organisation != request.user.organisation:
            return Response(
                {'detail': 'Invalid driver'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # If driver already has orders, add this order to their existing trip
        existing_trip = Trip.objects.filter(
            driver=driver,
            status__in=['scheduled', 'in_progress']
        ).first()

        if existing_trip:
            # Add order to existing trip
            order.trip = existing_trip
            order.driver = driver
            order.save()

            # Create new trip stops for this order
            TripService.add_order_to_trip(order, existing_trip)
        else:
            # Create new trip for the driver
            trip = TripService.create_simple_trip(
                orders=[order],
                driver=driver
            )
            if not trip:
                return Response(
                    {'detail': 'Failed to create trip'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reassign_driver(self, request, pk=None):
        order = self.get_object()
        new_driver_id = request.data.get('driver_id')
        
        if not new_driver_id:
            return Response(
                {'detail': 'Driver ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from users.models import Driver
            new_driver = Driver.objects.get(id=new_driver_id)
        except Driver.DoesNotExist:
            return Response(
                {'detail': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if driver belongs to the same organization
        if new_driver.organisation != request.user.organisation:
            return Response(
                {'detail': 'Invalid driver'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove order from current trip if any
        if order.trip:
            TripService.remove_order_from_trip(order)

        # Assign to new driver
        existing_trip = Trip.objects.filter(
            driver=new_driver,
            status__in=['scheduled', 'in_progress']
        ).first()

        if existing_trip:
            # Add order to existing trip
            order.trip = existing_trip
            order.driver = new_driver
            order.save()

            # Create new trip stops for this order
            TripService.add_order_to_trip(order, existing_trip)
        else:
            # Create new trip for the driver
            trip = TripService.create_simple_trip(
                orders=[order],
                driver=new_driver
            )
            if not trip:
                return Response(
                    {'detail': 'Failed to create trip'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(order)
        return Response(serializer.data)