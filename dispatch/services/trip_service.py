from datetime import datetime
from typing import List, Optional
import requests
from django.conf import settings
from django.utils import timezone

from dispatch.models import Trip, TripStop, Order, Location
from fleet.models import Vehicle

class TripService:
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
    def create_trip_from_optimization(optimization_result: dict, orders: List[Order]) -> Optional[Trip]:
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
                vehicle_id=vehicle_id,
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

            # Update orders with trip
            order_ids = set(step['shipment_id'] for step in steps if step['shipment_id'])
            Order.objects.filter(id__in=order_ids).update(trip=trip)

            return trip

    @staticmethod
    def create_simple_trip(orders: List[Order], vehicle: Optional[Vehicle] = None) -> Optional[Trip]:
        """Create a simple trip without optimization"""
        if not orders:
            return None

        # Use the first order's pickup as start and last order's dropoff as end
        start_location = orders[0].pickup
        end_location = orders[-1].drop_off

        # Create trip
        trip = Trip.objects.create(
            vehicle=vehicle,
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

        # Update orders with trip
        Order.objects.filter(id__in=[order.id for order in orders]).update(trip=trip)

        return trip