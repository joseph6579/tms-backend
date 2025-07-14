from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from dispatch.api.serializers.orders import OrderWriteSerializer, OrderListSerializer
from dispatch.models import Order


class OrderManagementViewset(ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    # serializer_class = OrderWriteSerializer
    serializer_class = OrderListSerializer

    @action(['post'], detail=False, url_path='create', serializer_class=OrderWriteSerializer)
    def create_order(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(organisation=request.user.organisation)
        data = OrderListSerializer(instance=obj).data
        return Response(data, status=status.HTTP_200_OK)
