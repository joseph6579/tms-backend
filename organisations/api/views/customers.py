from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from organisations.api.serializers.customers import (
    CustomerModelSerializer,
    CustomerWriteSerializer,
    CustomerListSerializer,
)
from organisations.models import Customer


class CustomerManagementViewset(ReadOnlyModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerListSerializer

    def get_queryset(self):
        user = self.request.user
        organisation_id = getattr(user, 'organisation_id')
        is_superuser = getattr(user, 'is_superuser')
        related_fields = ['location']
        fields = [
            'id',
            'name',
            'email',
            'phone_number',
            'is_active',
            'organisation_id',
            'location__name',
            'location__coordinates',
        ]
        qs = Customer.objects.select_related(*related_fields).only(*fields)

        if is_superuser:
            return qs.all()
        elif organisation_id:
            return qs.filter(organisation_id=organisation_id).all()
        else:
            return qs.none()

    @action(['post'], detail=False, url_path='create', serializer_class=CustomerWriteSerializer)
    def create_customer(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(organisation=request.user.organisation)
        data = CustomerListSerializer(instance=obj).data
        return Response(data, status=status.HTTP_200_OK)

    @action(['post'], detail=True, url_path='update', serializer_class=CustomerWriteSerializer)
    def create_customer(self, request, *args, **kwargs):
        customer = self.get_object()
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        obj = serializer.update(instance=customer, validated_data=serializer.validated_data)
        data = CustomerListSerializer(instance=obj).data
        return Response(data, status=status.HTTP_200_OK)
