from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from dispatch.models import Order
from dispatch.api.serializers.orders import OrderSerializer

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
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        order.status = 'completed'
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)