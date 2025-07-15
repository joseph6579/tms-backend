from typing import List, Optional

from django.db import transaction
from django.utils import timezone

from dispatch.constants import TripStopTypesChoices, OrderStatusChoices
from dispatch.models import Order, Trip, TripStop, Location
from dispatch.utils import get_or_create_location
from fleet.models import Vehicle
from users.models import Driver


class TripService:
    @staticmethod
    def format_orders_for_optimization(orders: List[Order], vehicles: List[Vehicle]) -> dict:
        """Format orders and vehicles for the optimization engine"""
        formatted_vehicles = []
        for vehicle in vehicles:
            formatted_vehicles.append(
                {
                    "id": str(vehicle.id),
                    "tonnage": 1000,  # Default tonnage, should be from vehicle specs
                    "start": {
                        "latitude": vehicle.driver.last_known_location.y
                        if vehicle.driver and vehicle.driver.last_known_location
                        else 0,
                        "longitude": vehicle.driver.last_known_location.x
                        if vehicle.driver and vehicle.driver.last_known_location
                        else 0,
                    },
                    "max_distance": 10000,  # Default max distance
                    "max_tasks": 5,  # Default max tasks
                }
            )

        formatted_shipments = []
        for order in orders:
            formatted_shipments.append(
                {
                    "id": str(order.id),
                    "origin": {"latitude": order.pickup.coordinates.y, "longitude": order.pickup.coordinates.x},
                    "destination": {
                        "latitude": order.drop_off.coordinates.y,
                        "longitude": order.drop_off.coordinates.x,
                    },
                    "total_weight": float(order.weight) if order.weight else 0,
                    "priority": order.priority,
                    "created": order.created_at.isoformat(),
                }
            )

        return {"vehicles": formatted_vehicles, "shipments": formatted_shipments}

    @staticmethod
    def create_trip_from_optimization(
        optimization_result: dict, orders: List[Order], driver: Optional[Driver] = None
    ) -> Optional[Trip]:
        """Create a trip from optimization engine result"""
        if not optimization_result:
            return None

        # Create trips for each vehicle route
        for route in optimization_result:
            vehicle_id = route.get('vehicle_id')
            steps = route.get('steps', [])

            if not steps:
                continue

            # Get first and last locations from steps
            start_step = steps[0]
            end_step = steps[-1]

            # Create or get locations
            start_location = Location.objects.create(
                name=f"Start Location {vehicle_id}",
                coordinates=f"POINT({start_step['longitude']} {start_step['latitude']})",
            )
            end_location = Location.objects.create(
                name=f"End Location {vehicle_id}", coordinates=f"POINT({end_step['longitude']} {end_step['latitude']})"
            )

            # Create trip
            trip = Trip.objects.create(
                vehicle_id=vehicle_id,
                driver=driver,
                start_location=start_location,
                end_location=end_location,
                scheduled_start_time=timezone.now(),
                distance=route.get('distance', 0),
                estimated_duration=route.get('travel_time', 0),
            )

            # Create trip stops
            for i, step in enumerate(steps):
                order = None
                if step['shipment_id']:
                    order = next((order for order in orders if str(order.id) == str(step['shipment_id'])), None)

                location = Location.objects.create(
                    name=f"Stop {i} for Trip {trip.id}", coordinates=f"POINT({step['longitude']} {step['latitude']})"
                )

                TripStop.objects.create(
                    trip=trip,
                    order=order,
                    location=location,
                    stop_type=step['type'],
                    sequence=i,
                    eta=timezone.now(),  # Should be calculated based on travel_time
                )

            # Update orders with trip and driver
            order_ids = set(step['shipment_id'] for step in steps if step['shipment_id'])
            Order.objects.filter(id__in=order_ids).update(trip=trip, driver=driver if driver else None)

            return trip

    @staticmethod
    def create_simple_trip(
        orders: List[Order], vehicle: Optional[Vehicle] = None, driver: Optional[Driver] = None
    ) -> Optional[Trip]:
        """Create a simple trip without optimization"""
        if not orders:
            return None

        # Use the first order's pickup as start and last order's dropoff as end
        start_location = orders[0].pickup
        end_location = orders[-1].drop_off

        # Create trip
        trip = Trip.objects.create(
            vehicle=vehicle,
            driver=driver,
            start_location=start_location,
            end_location=end_location,
            scheduled_start_time=timezone.now(),
        )

        # Create stops for each order
        sequence = 0
        for order in orders:
            # Create pickup stop
            TripStop.objects.create(
                trip=trip, order=order, location=order.pickup, stop_type='pickup', sequence=sequence
            )
            sequence += 1

            # Create dropoff stop
            TripStop.objects.create(
                trip=trip, order=order, location=order.drop_off, stop_type='drop_off', sequence=sequence
            )
            sequence += 1

        # Update orders with trip and driver
        Order.objects.filter(id__in=[order.id for order in orders]).update(trip=trip, driver=driver if driver else None)

        return trip

    @staticmethod
    def add_order_to_trip(order: Order, trip: Trip) -> None:
        """Add a new order to an existing trip"""
        # Get the highest sequence number
        last_sequence = trip.stops.order_by('-sequence').first().sequence

        # Create pickup stop
        TripStop.objects.create(
            trip=trip, order=order, location=order.pickup, stop_type='pickup', sequence=last_sequence + 1
        )

        # Create dropoff stop
        TripStop.objects.create(
            trip=trip, order=order, location=order.drop_off, stop_type='drop_off', sequence=last_sequence + 2
        )

        # Update trip end location
        trip.end_location = order.drop_off
        trip.save()

    @staticmethod
    def remove_order_from_trip(order: Order) -> None:
        """Remove an order from its current trip"""
        if not order.trip:
            return

        # Delete the order's stops
        order.trip.stops.filter(order=order).delete()

        # Update trip end location if this was the last order
        trip = order.trip
        last_stop = trip.stops.order_by('-sequence').first()
        if last_stop:
            trip.end_location = last_stop.location
            trip.save()

        # Remove trip association
        order.trip = None
        order.driver = None
        order.save()


class TripBuilder:
    """
    Service class used to create a trip, its trip stops and update the orders
    """

    def __init__(self, *, organisation, orders_data, start_loc_data, driver_profile=None, end_loc_data=None):
        """
        :param organisation: the trip's organisation
        :param orders_data: the order data
        :param start_loc_data: start location data
        :param driver_profile: the driver profile to be associated with the trip - Optional
        :param end_loc_data: end location data - Optional
        """
        self.org = organisation
        self.driver_profile = driver_profile
        self.orders_data = orders_data
        self.start_loc_data = start_loc_data
        self.end_loc_data = end_loc_data
        self.vehicle = getattr(driver_profile, 'vehicle', None)
        self.trip = None
        self.location_cache = {}
        self.trip_stops = []
        self.order_ids = []

    def _get_location(self, cache_key, **kwargs):
        if cache_key not in self.location_cache:
            self.location_cache[cache_key] = get_or_create_location(organisation_id=self.org.id, **kwargs)
        return self.location_cache[cache_key]

    @transaction.atomic
    def build(self):
        self._lock_orders()
        self._create_trip()
        self._create_stops()
        self._update_orders()
        return self.trip

    def _lock_orders(self):
        self.order_ids = [order_data['id'] for order_data in self.orders_data]
        self.orders_qs = Order.objects.select_for_update().filter(id__in=self.order_ids)

    def _create_trip(self):
        start_location = self._get_location("start", **self.start_loc_data)
        end_location = self._get_location("end", **self.end_loc_data) if self.end_loc_data else None

        self.trip = Trip.objects.create(
            driver_profile=self.driver_profile,
            vehicle=self.vehicle,
            organisation=self.org,
            status="assigned" if self.driver_profile else "pending",
            start_location=start_location,
            end_location=end_location,
            scheduled_start_time=timezone.now(),
        )

        self._add_stop(location=start_location, stop_type=TripStopTypesChoices.START.value, sequence=1)
        self.end_stop = TripStop(
            trip=self.trip,
            driver_profile=self.driver_profile,
            location=end_location or start_location,
            stop_type=TripStopTypesChoices.END.value,
        )

    def _add_stop(self, **kwargs):
        self.trip_stops.append(TripStop(**kwargs))

    def _create_stops(self):
        sequence = 2
        for order in self.orders_data:
            order_id = order["id"]
            origin = self._get_location(f"origin-{order_id}", **order["origin"])
            drop_off = self._get_location(f"dropoff-{order_id}", **order["drop_off"])

            self._add_stop(
                trip=self.trip,
                driver_profile=self.driver_profile,
                location=origin,
                sequence=sequence,
                stop_type=TripStopTypesChoices.AT_STORE.value,
                order_id=order_id,
            )
            sequence += 1
            self._add_stop(
                trip=self.trip,
                driver_profile=self.driver_profile,
                location=origin,
                sequence=sequence,
                stop_type=TripStopTypesChoices.PICKUP.value,
                order_id=order_id,
            )
            sequence += 1
            self._add_stop(
                trip=self.trip,
                driver_profile=self.driver_profile,
                location=drop_off,
                order_id=order_id,
                stop_type=TripStopTypesChoices.AT_DROP_OFF.value,
                sequence=sequence,
            )
            sequence += 1
            self._add_stop(
                trip=self.trip,
                driver_profile=self.driver_profile,
                location=drop_off,
                order_id=order_id,
                stop_type=TripStopTypesChoices.DROP_OFF.value,
                sequence=sequence,
            )
            sequence += 1

        self.end_stop.sequence = sequence
        self.trip_stops.append(self.end_stop)
        TripStop.objects.bulk_create(self.trip_stops)

    def _update_orders(self):
        status = OrderStatusChoices.ASSIGNED.value if self.driver_profile else OrderStatusChoices.BROADCASTED.value
        self.orders_qs.update(status=status, trip_id=self.trip.id, driver_profile=self.driver_profile)
