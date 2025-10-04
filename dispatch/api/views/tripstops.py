from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from dispatch.api.filters.trip_stops import TripStopFilter
from dispatch.api.serializers.trip_stops import TripStopListSerializer, TripStopCompletionSerializer
from dispatch.models import TripStop
from dispatch.services.trip_stop_completion import trip_stop_completion_svc


class TripStopViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TripStopListSerializer
    ordering_fields = ['order_id', 'driver_profile_id', 'trip_id', 'stop_type', 'sequence']
    search_fields = ['driver_profile__first_name', 'driver_profile__last_name', 'order__reference_number']
    filterset_class = TripStopFilter

    def get_queryset(self):
        user = self.request.user
        is_superuser = getattr(user, 'is_superuser', False)
        org_id = getattr(user, 'organisation_id', None)

        related_fields = ['order', 'trip', 'driver_profile', 'location', 'trip__organisation', 'driver_profile__driver']
        fields = [
            'id',
            'created_at',
            'updated_at',
            'completed_at',
            'notes',
            'stop_type',
            'sequence',
            'estimated_duration',
            'completed',
            'completed_by',
            'order_id',
            'order__reference_number',
            'order__status',
            'order__driver_profile_id',
            'trip_id',
            'trip__organisation_id',
            'driver_profile_id',
            'driver_profile__driver__email',
            'driver_profile__driver__phone_number',
            'location_id',
            'location__name',
            'location__address',
            'location__coordinates',
        ]
        qs = TripStop.objects.only(*fields).select_related(*related_fields)
        if is_superuser:
            return qs
        elif org_id:
            return qs.filter(trip__organisation_id=org_id)
        else:
            return qs.none()

    @action(methods=['post'], detail=True, url_path='complete', serializer_class=TripStopCompletionSerializer)
    def complete(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        driver_profile = data.get('driver_profile')
        notes = data.get('note', None)
        stop = self.get_object()
        trip_stop_completion_svc.complete_stop(stop=stop, driver_profile=driver_profile, note=notes)
        return Response({'detail': 'Action successful'}, status=status.HTTP_200_OK)
