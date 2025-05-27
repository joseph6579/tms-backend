from typing import List
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from redis import Redis
from dispatch.models import Order, Trip
from users.models import Driver

class BroadcastService:
    def __init__(self):
        self.redis = Redis(host='localhost', port=6379, db=0)
        self.BATCH_LOCK_TIMEOUT = 10  # seconds
        self.BROADCAST_RADIUS = 5  # km initial radius

    def lock_batch(self, batch_id: str) -> bool:
        """Lock a batch using Redis"""
        return self.redis.set(
            f"batch:{batch_id}:lock",
            "locked",
            ex=self.BATCH_LOCK_TIMEOUT,
            nx=True
        )

    def unlock_batch(self, batch_id: str) -> bool:
        """Unlock a batch"""
        return self.redis.delete(f"batch:{batch_id}:lock")

    def get_eligible_drivers(self, order: Order, radius: float) -> List[Driver]:
        """Get eligible drivers within radius"""
        return Driver.objects.filter(
            organisation=order.organization,
            status='available',
            is_active=True
        ).filter(
            Q(rating__gte=4.0) |  # Minimum rating requirement
            Q(rating__isnull=True)  # New drivers
        )

    def create_batch_from_orders(self, orders: List[Order]) -> dict:
        """Create a batch from orders"""
        if not orders:
            return None

        # Group orders by origin
        orders_by_origin = {}
        for order in orders:
            origin_key = f"{order.pickup.coordinates.y},{order.pickup.coordinates.x}"
            if origin_key not in orders_by_origin:
                orders_by_origin[origin_key] = []
            orders_by_origin[origin_key].append(order)

        # Sort each group by creation time
        for origin_key in orders_by_origin:
            orders_by_origin[origin_key].sort(key=lambda x: x.created_at)

        batches = []
        for origin_key, origin_orders in orders_by_origin.items():
            # Apply constraints
            current_batch = {
                'orders': [],
                'total_weight': 0,
                'total_volume': 0,
                'delivery_window': None
            }

            for order in origin_orders:
                # Check constraints
                if self.can_add_to_batch(current_batch, order):
                    current_batch['orders'].append(order)
                    current_batch['total_weight'] += float(order.weight or 0)
                    # Add volume calculation if needed
                else:
                    if current_batch['orders']:
                        batches.append(current_batch)
                        current_batch = {
                            'orders': [order],
                            'total_weight': float(order.weight or 0),
                            'total_volume': 0,
                            'delivery_window': order.delivery_window_end
                        }

            if current_batch['orders']:
                batches.append(current_batch)

        return batches

    def can_add_to_batch(self, batch: dict, order: Order) -> bool:
        """Check if order can be added to batch based on constraints"""
        MAX_BATCH_WEIGHT = 1000  # kg
        MAX_BATCH_SIZE = 5  # orders

        if len(batch['orders']) >= MAX_BATCH_SIZE:
            return False

        new_total_weight = batch['total_weight'] + float(order.weight or 0)
        if new_total_weight > MAX_BATCH_WEIGHT:
            return False

        # Check delivery window compatibility
        if batch['delivery_window'] and order.delivery_window_end:
            if order.delivery_window_end > batch['delivery_window']:
                return False

        return True

    @transaction.atomic
    def broadcast_batch(self, batch: dict) -> bool:
        """Broadcast batch to eligible drivers"""
        if not batch['orders']:
            return False

        # Generate unique batch ID
        import uuid
        batch_id = str(uuid.uuid4())

        # Lock the batch
        if not self.lock_batch(batch_id):
            return False

        try:
            # Get first order for location reference
            reference_order = batch['orders'][0]
            
            # Get eligible drivers
            radius = self.BROADCAST_RADIUS
            max_radius = 20  # km
            
            while radius <= max_radius:
                drivers = self.get_eligible_drivers(reference_order, radius)
                
                if drivers:
                    # Store batch information in Redis
                    self.redis.hmset(
                        f"batch:{batch_id}",
                        {
                            'status': 'broadcasting',
                            'created_at': timezone.now().isoformat(),
                            'order_ids': ','.join([str(order.id) for order in batch['orders']]),
                            'driver_ids': ','.join([str(driver.id) for driver in drivers])
                        }
                    )
                    self.redis.expire(f"batch:{batch_id}", 300)  # 5 minutes TTL

                    # Send notifications to drivers (implement FCM later)
                    self.send_batch_notifications(batch, drivers)
                    
                    # Update order metadata
                    for order in batch['orders']:
                        meta_data = order.meta_data or {}
                        meta_data.update({
                            'batch_id': batch_id,
                            'broadcast_time': timezone.now().isoformat(),
                            'broadcast_drivers': [str(d.id) for d in drivers]
                        })
                        order.meta_data = meta_data
                        order.save()

                    return True

                radius += 5  # Increase radius by 5km

            # If no drivers found even at max radius
            return False

        finally:
            self.unlock_batch(batch_id)

    def send_batch_notifications(self, batch: dict, drivers: List[Driver]) -> None:
        """Send FCM notifications to drivers"""
        # Implement FCM notification logic here
        pass

    def handle_batch_acceptance(self, batch_id: str, driver_id: str) -> bool:
        """Handle driver's acceptance of a batch"""
        batch_key = f"batch:{batch_id}"
        
        # Check if batch exists and is still valid
        if not self.redis.exists(batch_key):
            return False

        # Try to acquire acceptance lock
        if not self.redis.set(f"{batch_key}:accepted", driver_id, ex=30, nx=True):
            return False

        try:
            # Get batch details
            batch_data = self.redis.hgetall(batch_key)
            order_ids = batch_data.get('order_ids', '').split(',')

            # Create trip for the batch
            orders = Order.objects.filter(id__in=order_ids)
            driver = Driver.objects.get(id=driver_id)

            # Check if organization has route optimization
            if driver.organisation.has_route_optimization:
                from dispatch.services.trip_service import TripService
                # Create optimized trip
                optimization_data = TripService.format_orders_for_optimization(
                    orders=list(orders),
                    vehicles=[driver.vehicle] if driver.vehicle else []
                )
                # Call optimization service (implement actual API call)
                optimization_result = []  # Result from optimization service
                trip = TripService.create_trip_from_optimization(
                    optimization_result=optimization_result,
                    orders=list(orders),
                    driver=driver
                )
            else:
                # Create simple trip
                from dispatch.services.trip_service import TripService
                trip = TripService.create_simple_trip(
                    orders=list(orders),
                    driver=driver,
                    vehicle=driver.vehicle if driver.vehicle else None
                )

            if trip:
                # Update order statuses
                orders.update(
                    status='assigned',
                    driver=driver,
                    trip=trip
                )
                return True

            return False

        finally:
            # Clean up Redis keys
            self.redis.delete(f"{batch_key}:accepted")
            self.redis.delete(batch_key)