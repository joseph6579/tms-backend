from typing import List, Optional

from django.utils import timezone

from commons.constants import OrderStatusConfiguration, TripStopTypeChoices
from dispatch.models import Trip, TripStop, Order, Location
from fleet.models import Vehicle
from organisations.models import Organisation
from users.models import Driver


class TripService:

    @staticmethod
    def fetch_stops_configuration(org: Organisation) -> dict:
        """
        Fetches the stops configuration for the given organization. The method processes the
        organization's order status configuration, identifying active statuses that are designated
        as trip stops. It extracts notifications, service level agreements (SLA), and other
        relevant details for each active stop and organizes the data by stop type (e.g. pickup,
        dropoff).

        :param org: Organisation instance containing configuration details.
        :type org: Organisation
        :return: A dictionary with trip stop types as keys (e.g., pickup, dropoff) and lists
                 of active stop details as values.
        :rtype: dict
        """
        status_conf_json = org.configuration.order_status_configuration
        status_conf_model = OrderStatusConfiguration(**status_conf_json)

        result = {}
        result[TripStopTypeChoices.PICKUP.value] = []
        result[TripStopTypeChoices.DROPOFF.value] = []
        for field_name, field in status_conf_model.model_fields.items():
            alias = field.alias
            status_obj = getattr(status_conf_model, field_name)
            if status_obj.is_active and status_obj.is_trip_stop:
                notifications = status_obj.notifications.model_dump() if status_obj.notifications else None
                sla = status_obj.sla.model_dump() if status_obj.sla else None
                stop_type = status_obj.stop_type
                result[stop_type].append({'stop': alias, 'notifications': notifications, 'sla': sla})
        return result

    def construct_trip_step_data(self):
        """
        1. Fetch the organization's stop configuration using fetch_stops_configuration.
        2. For each trip, iterate through its stops and match the stop type with the
           configuration to gather relevant notifications and SLA details.
        3. Compile a structured representation of each trip's stops, including the stop type,
           associated notifications, and SLA information.
        :return:
        """
        pass



    @staticmethod
    def format_orders_for_optimization(orders: List[Order], vehicles: List[Vehicle]) -> dict:
        """Format orders and vehicles for the optimization engine"""
        formatted_vehicles = []
        for vehicle in vehicles:
            formatted_vehicles.append({
                "id": str(vehicle.id),
                "tonnage": 1000,  # Default tonnage, should be from vehicle specs
                "start": {
                    "latitude": vehicle.driver.last_known_location.y if vehicle.driver and vehicle.driver.last_known_location else 0,
                    "longitude": vehicle.driver.last_known_location.x if vehicle.driver and vehicle.driver.last_known_location else 0
                },
                "max_distance": 10000,  # Default max distance
                "max_tasks": 5  # Default max tasks
            })

        formatted_shipments = []
        for order in orders:
            formatted_shipments.append({
                "id": str(order.id),
                "origin": {
                    "latitude": order.pickup.coordinates.y,
                    "longitude": order.pickup.coordinates.x
                },
                "destination": {
                    "latitude": order.drop_off.coordinates.y,
                    "longitude": order.drop_off.coordinates.x
                },
                "total_weight": float(order.weight) if order.weight else 0,
                "priority": order.priority,
                "created": order.created_at.isoformat()
            })

        return {
            "vehicles": formatted_vehicles,
            "shipments": formatted_shipments
        }

    @staticmethod
    def create_trip_from_optimization(
        optimization_result: dict,
        orders: List[Order],
        organization: Organisation,
        driver: Optional[Driver] = None
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
                coordinates=f"POINT({start_step['longitude']} {start_step['latitude']})"
            )
            end_location = Location.objects.create(
                name=f"End Location {vehicle_id}",
                coordinates=f"POINT({end_step['longitude']} {end_step['latitude']})"
            )

            # Create trip
            trip = Trip.objects.create(
                organization=organization,
                vehicle_id=vehicle_id,
                driver=driver,
                start_location=start_location,
                end_location=end_location,
                scheduled_start_time=timezone.now(),
                distance=route.get('distance', 0),
                estimated_duration=route.get('travel_time', 0)
            )

            # Create trip stops
            for i, step in enumerate(steps):
                order = None
                if step['shipment_id']:
                    order = next(
                        (order for order in orders if str(order.id) == str(step['shipment_id'])),
                        None
                    )

                location = Location.objects.create(
                    name=f"Stop {i} for Trip {trip.id}",
                    coordinates=f"POINT({step['longitude']} {step['latitude']})"
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
            Order.objects.filter(id__in=order_ids).update(
                trip=trip,
                driver=driver if driver else None
            )

            return trip

    @staticmethod
    def create_simple_trip(
        orders: List[Order],
        vehicle: Optional[Vehicle] = None,
        driver: Optional[Driver] = None
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
            scheduled_start_time=timezone.now()
        )

        # Create stops for each order
        sequence = 0
        for order in orders:
            # Create pickup stop
            TripStop.objects.create(
                trip=trip,
                order=order,
                location=order.pickup,
                stop_type='pickup',
                sequence=sequence
            )
            sequence += 1

            # Create dropoff stop
            TripStop.objects.create(
                trip=trip,
                order=order,
                location=order.drop_off,
                stop_type='drop_off',
                sequence=sequence
            )
            sequence += 1

        # Update orders with trip and driver
        Order.objects.filter(id__in=[order.id for order in orders]).update(
            trip=trip,
            driver=driver if driver else None
        )

        return trip

    @staticmethod
    def add_order_to_trip(order: Order, trip: Trip) -> None:
        """Add a new order to an existing trip"""
        # Get the highest sequence number
        last_sequence = trip.stops.order_by('-sequence').first().sequence

        # Create pickup stop
        TripStop.objects.create(
            trip=trip,
            order=order,
            location=order.pickup,
            stop_type='pickup',
            sequence=last_sequence + 1
        )

        # Create dropoff stop
        TripStop.objects.create(
            trip=trip,
            order=order,
            location=order.drop_off,
            stop_type='drop_off',
            sequence=last_sequence + 2
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


trip_svc = TripService()