from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from dispatch.api.filters.trip_stops import TripStopFilter
from dispatch.api.serializers.trip_stops import TripStopListSerializer, TripStopCompletionSerializer
from dispatch.models import TripStop
from dispatch.api.serializers.trips import TripStopSerializer
from dispatch.utils import stop_type_to_order_status


class TripStopViewSetOld(viewsets.ModelViewSet):
    serializer_class = TripStopSerializer

    def get_queryset(self):
        return TripStop.objects.filter(trip__driver__organisation=self.request.user.organisation)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a trip stop as completed"""
        stop = self.get_object()

        if stop.status == 'completed':
            return Response({'detail': 'Stop already completed'}, status=status.HTTP_400_BAD_REQUEST)

        if stop.trip.status not in ['in_progress', 'scheduled']:
            return Response({'detail': 'Trip is not in progress'}, status=status.HTTP_400_BAD_REQUEST)

        stop.status = 'completed'
        stop.completed_at = timezone.now()
        stop.completed_by = request.user
        stop.save()

        # Update order status if this is a delivery stop
        if stop.stop_type == 'drop_off' and stop.order:
            stop.order.status = 'completed'
            stop.order.date_delivered = timezone.now()
            stop.order.save()

        # Check if all stops are completed
        if not stop.trip.stops.exclude(status='completed').exists():
            stop.trip.status = 'completed'
            stop.trip.completed_time = timezone.now()
            stop.trip.save()

        serializer = self.get_serializer(stop)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def arrive(self, request, pk=None):
        """Mark arrival at a trip stop"""
        stop = self.get_object()

        if stop.status != 'pending':
            return Response({'detail': 'Stop is not pending'}, status=status.HTTP_400_BAD_REQUEST)

        stop.status = 'arrived'
        stop.actual_arrival = timezone.now()
        stop.save()

        serializer = self.get_serializer(stop)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """Mark a trip stop as skipped"""
        stop = self.get_object()

        if stop.status in ['completed', 'skipped']:
            return Response({'detail': 'Stop already completed or skipped'}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason')
        if not reason:
            return Response({'detail': 'Reason is required for skipping a stop'}, status=status.HTTP_400_BAD_REQUEST)

        stop.status = 'skipped'
        stop.notes = reason
        stop.save()

        serializer = self.get_serializer(stop)
        return Response(serializer.data)


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

    @transaction.atomic()
    @action(methods=['post'], detail=True, url_path='complete', serializer_class=TripStopCompletionSerializer)
    def complete(self, request, *args, **kwargs):
        user = request.user
        stop = self.get_object()
        if not stop.completed:
            if order := stop.order:
                if user.id == stop.driver_profile_id or user.id == order.driver_profile_id:
                    new_status = stop_type_to_order_status(stop_type=stop.stop_type)
                    order.status = new_status
                    order.date_delivered = timezone.now() if new_status == 'delivered' else None
                    order.save(update_fields=['status', 'date_delivered'])
                    stop.completed_at = timezone.now()
                    stop.completed_by = user
                    stop.completed = True
                    stop.save(update_fields=['completed_at', 'completed_by', 'completed'])
                else:
                    return Response({'detail': 'Action not allowed'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': 'Action successful'}, status=status.HTTP_200_OK)
