from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from dispatch.models import TripStop
from dispatch.api.serializers.trips import TripStopSerializer

class TripStopViewSet(viewsets.ModelViewSet):
    serializer_class = TripStopSerializer
    
    def get_queryset(self):
        return TripStop.objects.filter(
            trip__driver__organisation=self.request.user.organisation
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a trip stop as completed"""
        stop = self.get_object()
        
        if stop.status == 'completed':
            return Response(
                {'detail': 'Stop already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if stop.trip.status not in ['in_progress', 'scheduled']:
            return Response(
                {'detail': 'Trip is not in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            return Response(
                {'detail': 'Stop is not pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            return Response(
                {'detail': 'Stop already completed or skipped'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason')
        if not reason:
            return Response(
                {'detail': 'Reason is required for skipping a stop'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stop.status = 'skipped'
        stop.notes = reason
        stop.save()

        serializer = self.get_serializer(stop)
        return Response(serializer.data)