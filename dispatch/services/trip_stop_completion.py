from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from commons.constants import OrderStatusChoices, TripStopTypeChoices, TripStatusChoices
from dispatch.models import TripStop, Order, Trip
from fleet.models import DriverProfile


class TripStopCompletionService:
    @staticmethod
    def verify_stop_ownership(stop: TripStop, driver_profile: DriverProfile):
        if stop.trip.driver_profile != driver_profile:
            raise ValidationError(_("Stop is not assigned to you"))

    @staticmethod
    def verify_trip_ownership(trip_stop: TripStop, driver_profile: DriverProfile):
        if trip_stop.trip.driver_profile != driver_profile:
            raise ValidationError(_("Trip is not assigned to you"))

    @staticmethod
    def verify_order_ownership(order: Order, driver_profile: DriverProfile):
        if order.trip.driver_profile != driver_profile:
            raise ValidationError(_("Order is not assigned to you"))

    @staticmethod
    def verify_stop_not_completed(stop: TripStop):
        if stop.completed:
            raise ValidationError(_("Stop is already completed"))

    @staticmethod
    def verify_stop_sequence(stop: TripStop):
        trip = stop.trip
        previous_stops = trip.stops.filter(sequence__lt=stop.sequence)
        for prev_stop in previous_stops:
            if not prev_stop.completed:
                raise ValidationError(_("Previous stops must be completed first"))

    @staticmethod
    def mark_stop_completed(stop: TripStop, completed_by: DriverProfile, notes: str = None):
        stop.completed = True
        stop.completed_by = completed_by
        if notes:
            stop.notes = notes
        # stop.save()

    @staticmethod
    def stop_type_to_order_status(stop_type: str) -> str:
        order_status_mapping = {
            OrderStatusChoices.ARRIVED_AT_PICKUP.value: TripStopTypeChoices.AT_PICKUP.value,
            OrderStatusChoices.IN_PROGRESS.value: TripStopTypeChoices.PICKUP.value,
            OrderStatusChoices.ARRIVED_AT_DROP_OFF.value: TripStopTypeChoices.AT_DROP_OFF.value,
            OrderStatusChoices.COMPLETED.value: TripStopTypeChoices.DROPOFF.value,
        }
        return order_status_mapping.get(stop_type)

    def update_order_status_if_applicable(self, stop: TripStop):
        if stop.order:
            new_status = self.stop_type_to_order_status(stop.stop_type)
            order = stop.order
            if new_status and stop.order.status != new_status:
                order.status = new_status
                fields = ['status']
                if new_status == OrderStatusChoices.COMPLETED.value:
                    order.date_delivered = timezone.now()
                    fields.append('date_delivered')
                order.save(update_fields=fields)

    @staticmethod
    def start_trip(trip: Trip):
        if trip.status not in [
            TripStatusChoices.SCHEDULED.value,
            TripStatusChoices.PENDING.value,
            TripStatusChoices.ASSIGNED.value,
        ]:
            raise ValidationError(_("Trip cannot be started"))
        trip.status = TripStatusChoices.ON_GOING.value
        trip.actual_start_time = timezone.now()
        trip.save(update_fields=['status', 'actual_start_time'])

    @staticmethod
    def complete_trip(trip: Trip):
        if trip.status != TripStatusChoices.ON_GOING.value:
            raise ValidationError(_("Trip cannot be completed"))
        if (
            TripStop.objects.filter(trip=trip, completed=False)
            .exclude(stop_type=TripStopTypeChoices.END.value)
            .exists()
        ):
            raise ValidationError(_("All stops must be completed before completing the trip"))
        trip.status = TripStatusChoices.COMPLETED.value
        trip.completed_time = timezone.now()
        trip.save(update_fields=['status', 'completed_time'])

    @transaction.atomic
    def complete_stop(self, stop: TripStop, driver_profile: DriverProfile, notes: str = None):
        self.verify_stop_ownership(stop, driver_profile)
        self.verify_trip_ownership(stop, driver_profile)
        self.verify_stop_not_completed(stop)
        if stop.stop_type == TripStopTypeChoices.START.value:
            self.start_trip(stop.trip)
        elif stop.stop_type == TripStopTypeChoices.END.value:
            self.complete_trip(stop.trip)
        # self.verify_stop_sequence(stop)
        self.mark_stop_completed(stop, driver_profile, notes)
        stop.save(update_fields=['completed', 'completed_by', 'completed_at', 'notes'])
        self.update_order_status_if_applicable(stop)


trip_stop_completion_svc = TripStopCompletionService()
