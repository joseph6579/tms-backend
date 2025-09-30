from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from dispatch.models import Order, OrderReview
from dispatch.api.serializers.orders import OrderSerializer, OrderReviewSerializer, DispatchOrdersSerializer
from dispatch.services.broadcast_service import BroadcastService
from dispatch.services.trip_service import trip_svc
from users.models import Driver


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(organization=self.request.user.organisation)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Add a review for the order"""
        order = self.get_object()
        
        # Check if order is completed
        if order.status != 'completed':
            return Response(
                {'detail': 'Can only review completed orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if order already has a review
        if OrderReview.objects.filter(order=order).exists():
            return Response(
                {'detail': 'Order already has a review'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderReviewSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(order=order, driver=order.driver)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        """Broadcast orders to available drivers"""
        order_ids = request.data.get('order_ids', [])
        
        # Get orders
        orders = Order.objects.filter(
            id__in=order_ids,
            organization=request.user.organisation,
            status='pending',
            trip__isnull=True
        )

        if not orders:
            return Response(
                {'detail': 'No valid orders found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize broadcast service
        broadcast_service = BroadcastService()

        # Create batches
        batches = broadcast_service.create_batch_from_orders(list(orders))

        if not batches:
            return Response(
                {'detail': 'Could not create batches from orders'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Broadcast each batch
        results = []
        for batch in batches:
            success = broadcast_service.broadcast_batch(batch)
            results.append({
                'orders': [str(order.id) for order in batch['orders']],
                'broadcast_success': success
            })

        return Response(results)

    @action(detail=False, methods=['post'])
    def accept_batch(self, request):
        """Accept a broadcasted batch"""
        batch_id = request.data.get('batch_id')
        driver_id = request.data.get('driver_id')

        if not batch_id or not driver_id:
            return Response(
                {'detail': 'Batch ID and Driver ID are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        broadcast_service = BroadcastService()
        success = broadcast_service.handle_batch_acceptance(batch_id, driver_id)

        if success:
            return Response({'detail': 'Batch accepted successfully'})
        else:
            return Response(
                {'detail': 'Failed to accept batch'},
                status=status.HTTP_400_BAD_REQUEST
            )


    @action(detail=False, methods=['post'], serializer_class=DispatchOrdersSerializer, url_path='dispatch')
    def dispatch_orders(self, request, *args, **kwargs):
        """Dispatch orders to drivers"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        order_ids = data.get('order_ids', [])
        driver_id = data.get('driver_id', None)

        orders = Order.objects.filter(id__in=order_ids)
        driver = Driver.objects.get(id=driver_id) if driver_id else None

        if not trip_svc.validate_order_statuses(orders=orders):
            return Response(
                {'detail': 'One or more orders are not in a dispatchable state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if driver:
            if not trip_svc.validate_driver_availability(driver=driver):
                return Response(
                    {'detail': 'Driver is not available for dispatch'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        trip = trip_svc.create_trip_from_orders(orders=orders, driver=driver)
        trip_svc.construct_bare_trip_step_data(trip=trip, orders=orders, driver=driver)
        trip_svc.update_trip_orders(trip=trip, orders=orders)

        return Response(
            {'detail': f'Dispatched {len(orders)} orders'},
            status=status.HTTP_200_OK
        )