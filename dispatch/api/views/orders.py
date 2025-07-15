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
        obj = serializer.save(organisation=request.user.organisation)
        data = OrderListSerializer(instance=obj).data
        return Response(data, status=status.HTTP_200_OK)
