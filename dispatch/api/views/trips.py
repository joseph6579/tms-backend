from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from dispatch.models import Trip, Order
from dispatch.services.trip_service import TripService
from fleet.models import Vehicle
from dispatch.api.serializers.trips import TripSerializer

class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Trip.objects.filter(
            orders__organization=self.request.user.organisation
        ).distinct()

    @action(detail=False, methods=['post'])
    def create_from_orders(self, request):
        order_ids = request.data.get('order_ids', [])
        optimize = request.data.get('optimize', False)
        vehicle_id = request.data.get('vehicle_id')

        # Get orders
        orders = Order.objects.filter(
            id__in=order_ids,
            organization=request.user.organisation,
            trip__isnull=True
        )

        if not orders:
            return Response(
                {'detail': 'No valid orders found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        vehicle = None
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
            except Vehicle.DoesNotExist:
                return Response(
                    {'detail': 'Vehicle not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        if optimize and request.user.organisation.has_route_optimization:
            # Format data for optimization
            optimization_data = TripService.format_orders_for_optimization(
                orders=orders,
                vehicles=[vehicle] if vehicle else Vehicle.objects.filter(source='in_house')
            )

            # Call optimization service
            # This is a placeholder - implement actual API call
            optimization_result = []  # Result from optimization service

            # Create trip from optimization result
            trip = TripService.create_trip_from_optimization(
                optimization_result=optimization_result,
                orders=orders
            )
        else:
            # Create simple trip without optimization
            trip = TripService.create_simple_trip(orders=orders, vehicle=vehicle)

        if not trip:
            return Response(
                {'detail': 'Failed to create trip'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(trip)
        return Response(serializer.data, status=status.HTTP_201_CREATED)