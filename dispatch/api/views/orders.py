from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from dispatch.api.filters.orders import OrderFilter
from dispatch.api.serializers.orders import OrderWriteSerializer, OrderListSerializer
from dispatch.models import Order


class OrderManagementViewset(ReadOnlyModelViewSet):
    filterset_class = OrderFilter
    search_fields = [
        'reference_number',
        'driver__first_name',
        'driver__last_name',
        'recipient__name',
        'recipient__email',
        'recipient__phone_numer',
        'buyer__name',
        'buyer__email',
        'buyer__phone_numer',
    ]
    ordering_fields = ['created_at', 'updated_at', 'date_delivered']
    serializer_class = OrderListSerializer


from dispatch.models import Order, OrderReview
from dispatch.api.serializers.orders import OrderSerializer, OrderReviewSerializer, DispatchOrdersSerializer
from dispatch.services.broadcast_service import BroadcastService
from dispatch.services.trip_service import trip_svc
from users.models import Driver


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    
    
    def get_queryset(self):
        user = self.request.user
        is_superuser = getattr(user, 'is_superuser', False)
        org_id = getattr(user, 'organisation_id', None)

        related_fields = [
            'driver_profile',
            'recipient',
            'pickup',
            'drop_off',
            'store',
            'buyer',
            'organisation',
            'driver_profile__driver',
        ]
        fields = [
            'id',
            'created_at',
            'updated_at',
            'reference_number',
            'status',
            'priority',
            'date_delivered',
            'date_cancelled',
            'date_failed',
            'description',
            'instructions',
            'driver_profile__id',
            'driver_profile__first_name',
            'driver_profile__last_name',
            'driver_profile__driver__phone_number',
            'driver_profile__driver__email',
            'recipient__id',
            'recipient__name',
            'recipient__email',
            'recipient__phone_number',
            'buyer__id',
            'buyer__name',
            'buyer__email',
            'buyer__phone_number',
            'store__id',
            'store__name',
            'pickup__id',
            'pickup__name',
            'pickup__address',
            'pickup__coordinates',
            'drop_off__id',
            'drop_off__name',
            'drop_off__address',
            'drop_off__coordinates',
            'organisation_id',
            'trip_id',
        ]
        qs = Order.objects.only(*fields).select_related(*related_fields)
        if is_superuser:
            return qs
        elif org_id:
            return qs.filter(organisation_id=org_id)
        else:
            return qs.none()

    @transaction.atomic()
    @action(['post'], detail=False, url_path='create', serializer_class=OrderWriteSerializer)
    def create_order(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
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
      
#         obj = serializer.save(organisation=request.user.organisation)
#         data = OrderListSerializer(instance=obj).data
#         return Response(data, status=status.HTTP_200_OK)
