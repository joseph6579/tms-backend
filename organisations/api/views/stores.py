from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from commons.permissions import HasCompany
from organisations.api.filters.stores import StoreFilter
from organisations.api.serializers.stores import StoreModelSerializer, StoreWriteSerializer
from organisations.models import Store


class StoreManagementViewset(ReadOnlyModelViewSet):
    serializer_class = StoreModelSerializer
    search_fields = ['name', 'key']
    ordering_fields = ['created_at', 'broadcast_radius']
    filterset_class = StoreFilter

    def get_queryset(self):
        user = self.request.user
        organisation_id = getattr(user, 'organisation_id')
        is_superuser = getattr(user, 'is_superuser')
        fields = ['id', 'name', 'key', 'location', 'broadcast_radius', 'organisation_id']

        qs = Store.objects.only(*fields)
        if is_superuser:
            return qs.all()
        elif organisation_id:
            return qs.filter(organisation_id=organisation_id)
        else:
            return qs.none()

    @action(
        ['post'],
        detail=False,
        url_path='create',
        serializer_class=StoreWriteSerializer,
        permission_classes=[HasCompany],
    )
    def create_store(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(organisation=request.user.organisation)
        data = StoreModelSerializer(instance=obj).data
        return Response(data, status=status.HTTP_200_OK)

    @action(
        ['post'], detail=True, url_path='update', serializer_class=StoreWriteSerializer, permission_classes=[HasCompany]
    )
    def update_store(self, request, *args, **kwargs):
        store = self.get_object()
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context(), instance=store)
        serializer.is_valid(raise_exception=True)
        obj = serializer.update(instance=store, validated_data=serializer.validated_data)
        data = StoreModelSerializer(instance=obj).data
        return Response(data, status=status.HTTP_200_OK)
