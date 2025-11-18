# Status Transition DAOs and Service
"""
This document contains a ready-to-adopt implementation scaffold for:

- DAO layer: OrderDAO, TripDAO, TripStepDAO, DriverDAO, RedropDAO, OrderAssignmentLogDAO
- Status transition handlers for the transitions described in your PDF
- Orchestrator: OrderStatusTransitionService (bulk-capable)
- Redis lock helper usage and DB select_for_update locking via DAOs
- Celery task hooks for notifications and reindexing

> **Note**: This is an implementation scaffold. Replace imports and model names if your codebase places models under different modules. The field names match the confirmation you provided: `Order` has `trip`, `driver`, `status`, `delivered_at`, `original_order` etc.; `Trip` has `status`, `driver`; `TripStep` has `completed`, `completed_at`; `Driver` has `status` (labelled `status`) and `is_available`.

"""

## 1) File: `orders/daos.py`


# orders/daos.py
from typing import List, Optional
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

# Replace these imports with your project's model import paths
from orders.models import Order, OrderAssignmentLog
from trips.models import Trip, TripStep
from drivers.models import Driver


class OrderDAO:
    @staticmethod
    def get_orders(order_ids: List[int]) -> QuerySet:
        return Order.objects.filter(id__in=order_ids)

    @staticmethod
    def lock_orders_for_update(order_ids: List[int]) -> QuerySet:
        return Order.objects.select_for_update().filter(id__in=order_ids)

    @staticmethod
    def update_status(order: Order, new_status: str, extra_fields: dict = None):
        fields = ['status']
        order.status = new_status
        if extra_fields:
            for k, v in extra_fields.items():
                setattr(order, k, v)
                fields.append(k)
        order.save(update_fields=list(set(fields)))
        return order

    @staticmethod
    def set_trip(order: Order, trip: Optional[Trip]):
        order.trip = trip
        order.save(update_fields=['trip'])

    @staticmethod
    def create_redrop_from(order: Order, copy_fields: List[str] = None) -> Order:
        # Minimal copy; adapt to your schema
        copy_fields = copy_fields or [
            'sender',
            'recipient',
            'recipient_phone',
            'recipient_email',
            'package',
            'pickup_address',
            'delivery_address',
        ]
        data = {f: getattr(order, f) for f in copy_fields if hasattr(order, f)}
        data['status'] = 'PENDING'
        data['original_order'] = order
        redrop = Order.objects.create(**data)
        return redrop


class TripDAO:
    @staticmethod
    def get_trip_for_update(trip_id: int) -> Trip:
        return Trip.objects.select_for_update().get(id=trip_id)

    @staticmethod
    def mark_trip_stale(trip: Trip):
        trip.status = 'STALE'
        trip.save(update_fields=['status'])

    @staticmethod
    def mark_trip_completed(trip: Trip):
        trip.status = 'COMPLETED'
        trip.save(update_fields=['status'])

    @staticmethod
    def get_remaining_orders(trip: Trip, exclude_order_ids: List[int] = None):
        qs = trip.orders.all()
        if exclude_order_ids:
            qs = qs.exclude(id__in=exclude_order_ids)
        return qs


class TripStepDAO:
    @staticmethod
    def delete_steps_for_order(order_id: int):
        TripStep.objects.filter(order_id=order_id).delete()

    @staticmethod
    def delete_incomplete_steps_for_trip(trip: Trip):
        TripStep.objects.filter(trip=trip, completed=False).delete()

    @staticmethod
    def complete_steps_for_order(order_id: int):
        TripStep.objects.filter(order_id=order_id, completed=False).update(completed=True, completed_at=timezone.now())


class DriverDAO:
    @staticmethod
    def free_driver(driver: Driver):
        # keep driver.status field name as 'status' (per your confirmation)
        driver.status = 'AVAILABLE'
        if hasattr(driver, 'is_available'):
            driver.is_available = True
            driver.save(update_fields=['status', 'is_available'])
        else:
            driver.save(update_fields=['status'])


class OrderAssignmentLogDAO:
    @staticmethod
    def create_log(
        order: Order,
        actor_id: Optional[int],
        actor_app: Optional[str],
        prev_status: str,
        new_status: str,
        reason: Optional[str],
        metadata: dict = None,
    ):
        return OrderAssignmentLog.objects.create(
            order=order,
            actor_id=actor_id,
            actor_app=actor_app,
            previous_status=prev_status,
            new_status=new_status,
            reason=reason,
            metadata=metadata or {},
        )


## 2) File: `orders/locks.py` — Redis lock helper (app-level lock)

# orders/locks.py
import contextlib
import time
import uuid
from typing import Iterator
import redis
from django.conf import settings

REDIS_CLIENT = redis.Redis.from_url(getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'))


class LockAcquireError(RuntimeError):
    pass


@contextlib.contextmanager
def redis_lock(key: str, timeout: int = 30, wait: float = 0.1) -> Iterator[str]:
    token = str(uuid.uuid4())
    end = time.time() + timeout
    while time.time() < end:
        if REDIS_CLIENT.set(key, token, nx=True, ex=timeout):
            try:
                yield token
            finally:
                val = REDIS_CLIENT.get(key)
                if val and val.decode() == token:
                    REDIS_CLIENT.delete(key)
            return
        time.sleep(wait)
    raise LockAcquireError(f"Couldn't acquire lock {key}")


## 3) File: `orders/handlers.py` — Transition handler base and implementations

# orders/handlers.py
from abc import ABC, abstractmethod
from typing import Dict
from django.utils import timezone
from trips.trip_builder import TripBuilder  # your TripBuilder

from orders.daos import OrderDAO, TripDAO, TripStepDAO, DriverDAO, OrderAssignmentLogDAO


class TransitionError(Exception):
    pass


class BaseHandler(ABC):
    def __init__(self, order, context):
        self.order = order
        self.context = context

    @abstractmethod
    def run(self) -> Dict:
        """Execute transition, return metadata dict"""
        pass


# Helper to update and log
class _LoggingMixin:
    def log(self, prev, new, metadata=None):
        OrderAssignmentLogDAO.create_log(
            order=self.order,
            actor_id=self.context.actor_id,
            actor_app=self.context.actor_app,
            prev_status=prev,
            new_status=new,
            reason=self.context.reason,
            metadata=metadata or {},
        )


# Examples of handlers mapped to the PDF rules. Add the rest similarly.


class AssignedToPendingHandler(_LoggingMixin, BaseHandler):
    def run(self):
        prev = self.order.status
        if prev != 'ASSIGNED':
            raise TransitionError('INVALID_PREVIOUS_STATUS')
        metadata = {}
        trip = getattr(self.order, 'trip', None)
        if trip:
            # delete this order's trip steps
            TripStepDAO.delete_steps_for_order(self.order.id)
            # detach order from trip
            OrderDAO.set_trip(self.order, None)
            metadata['old_trip_id'] = trip.id

            # remaining orders
            remaining = TripDAO.get_remaining_orders(trip, exclude_order_ids=[self.order.id])
            if remaining.exists():
                # delete incomplete steps and build a new trip for remaining orders
                TripStepDAO.delete_incomplete_steps_for_trip(trip)
                builder = TripBuilder(orders=remaining, optimize=self.context.optimize_routes)
                new_trip = builder.build()
                metadata['new_trip_id'] = new_trip.id
                self.context.created_trips.append(new_trip.id)
                TripDAO.mark_trip_stale(trip)
            else:
                # mark trip completed and free driver
                TripDAO.mark_trip_completed(trip)
                if trip.driver:
                    DriverDAO.free_driver(trip.driver)
                metadata['trip_completed'] = True

        OrderDAO.update_status(self.order, 'PENDING')
        self.log(prev, 'PENDING', metadata)
        return metadata


class AssignedToDeliveredHandler(_LoggingMixin, BaseHandler):
    def run(self):
        prev = self.order.status
        if prev not in ('ASSIGNED', 'IN_TRANSIT', 'ARRIVED_AT_STORE'):
            raise TransitionError('INVALID_PREVIOUS_STATUS')
        metadata = {}
        trip = getattr(self.order, 'trip', None)
        # mark steps completed
        TripStepDAO.complete_steps_for_order(self.order.id)
        # delete steps
        TripStepDAO.delete_steps_for_order(self.order.id)
        # set delivered
        OrderDAO.update_status(self.order, 'DELIVERED', {'delivered_at': timezone.now()})
        metadata['delivered_at'] = str(timezone.now())

        if trip:
            remaining = TripDAO.get_remaining_orders(trip, exclude_order_ids=[self.order.id])
            if remaining.exists():
                # rebuild trip
                TripStepDAO.delete_incomplete_steps_for_trip(trip)
                builder = TripBuilder(orders=remaining, optimize=self.context.optimize_routes)
                new_trip = builder.build()
                metadata['new_trip_id'] = new_trip.id
                self.context.created_trips.append(new_trip.id)
                TripDAO.mark_trip_stale(trip)
            else:
                TripDAO.mark_trip_completed(trip)
                if trip.driver:
                    DriverDAO.free_driver(trip.driver)
                metadata['trip_completed'] = True

        self.log(prev, 'DELIVERED', metadata)
        return metadata


class BroadcastedToPendingHandler(_LoggingMixin, BaseHandler):
    def run(self):
        prev = self.order.status
        if prev != 'BROADCASTED':
            raise TransitionError('INVALID_PREVIOUS_STATUS')
        metadata = {}
        trip = getattr(self.order, 'trip', None)
        if trip:
            TripStepDAO.delete_steps_for_order(self.order.id)
            OrderDAO.set_trip(self.order, None)
            TripDAO.mark_trip_stale(trip)
            metadata['old_trip_id'] = trip.id
            remaining = TripDAO.get_remaining_orders(trip, exclude_order_ids=[self.order.id]).filter(
                status='BROADCASTED'
            )
            if remaining.exists():
                TripStepDAO.delete_incomplete_steps_for_trip(trip)
                builder = TripBuilder(orders=remaining, optimize=self.context.optimize_routes)
                new_trip = builder.build()
                # assume Trip has broadcast() method
                new_trip.broadcast()
                metadata['new_trip_id'] = new_trip.id
                self.context.created_trips.append(new_trip.id)
        OrderDAO.update_status(self.order, 'PENDING')
        self.log(prev, 'PENDING', metadata)
        return metadata


class BroadcastedToFailedHandler(_LoggingMixin, BaseHandler):
    def run(self):
        prev = self.order.status
        if prev != 'BROADCASTED':
            raise TransitionError('INVALID_PREVIOUS_STATUS')
        metadata = {}
        # create redrop
        redrop = OrderDAO.create_redrop_from(self.order)
        self.context.redrops.append(redrop.id)
        metadata['redrop_id'] = redrop.id

        trip = getattr(self.order, 'trip', None)
        if trip:
            TripStepDAO.delete_steps_for_order(self.order.id)
            OrderDAO.set_trip(self.order, None)
            TripDAO.mark_trip_stale(trip)
            metadata['old_trip_id'] = trip.id
            remaining = TripDAO.get_remaining_orders(trip, exclude_order_ids=[self.order.id])
            if remaining.exists():
                TripStepDAO.delete_incomplete_steps_for_trip(trip)
                builder = TripBuilder(orders=remaining, optimize=self.context.optimize_routes)
                new_trip = builder.build()
                new_trip.broadcast()
                metadata['new_trip_id'] = new_trip.id
                self.context.created_trips.append(new_trip.id)
            else:
                TripDAO.mark_trip_completed(trip)
                if trip.driver:
                    DriverDAO.free_driver(trip.driver)
                metadata['trip_completed'] = True

        OrderDAO.update_status(self.order, 'FAILED')
        self.log(prev, 'FAILED', metadata)
        return metadata


# You should implement handlers for all allowed transitions following the PDF rules.


## 4) File: `orders/service.py` — Orchestrator


# orders/service.py
from collections import defaultdict
from typing import List, Dict
from django.db import transaction
from orders.locks import redis_lock, LockAcquireError
from orders.daos import OrderDAO, TripDAO
from orders.handlers import (
    AssignedToPendingHandler,
    AssignedToDeliveredHandler,
    BroadcastedToPendingHandler,
    BroadcastedToFailedHandler,
)

ALLOWED_TRANSITIONS = {
    'SCHEDULED': {'PENDING', 'CANCELLED'},
    'PENDING': {'CANCELLED', 'FAILED'},
    'BROADCASTED': {'PENDING', 'CANCELLED', 'FAILED'},
    'ASSIGNED': {'PENDING', 'CANCELLED', 'FAILED', 'DELIVERED'},
    'ARRIVED_AT_STORE': {'PENDING', 'CANCELLED', 'FAILED', 'DELIVERED'},
    'IN_TRANSIT': {'PENDING', 'CANCELLED', 'FAILED', 'DELIVERED'},
    'ARRIVED_AT_DESTINATION': {'PENDING', 'CANCELLED', 'FAILED', 'DELIVERED'},
    'DELIVERED': set(),
    'CANCELLED': set(),
    'FAILED': set(),
}

HANDLER_MAP = {
    ('ASSIGNED', 'PENDING'): AssignedToPendingHandler,
    ('ASSIGNED', 'DELIVERED'): AssignedToDeliveredHandler,
    ('BROADCASTED', 'PENDING'): BroadcastedToPendingHandler,
    ('BROADCASTED', 'FAILED'): BroadcastedToFailedHandler,
    # add others
}


class TransitionContext:
    def __init__(self, actor_id=None, actor_app=None, reason=None, optimize_routes=True):
        self.actor_id = actor_id
        self.actor_app = actor_app
        self.reason = reason
        self.optimize_routes = optimize_routes
        self.created_trips = []
        self.redrops = []


class OrderStatusTransitionService:
    def change_status_bulk(
        self, actor_id: int, order_ids: List[int], new_status: str, *, reason: str = None, optimize_routes: bool = True
    ) -> Dict:
        ctx = TransitionContext(actor_id=actor_id, actor_app=None, reason=reason, optimize_routes=optimize_routes)
        orders_qs = OrderDAO.get_orders(order_ids)
        existing_ids = set(orders_qs.values_list('id', flat=True))
        missing = set(order_ids) - existing_ids
        result = {'success': [], 'failed': []}
        for mid in missing:
            result['failed'].append({'order_id': mid, 'error': 'NOT_FOUND'})

        orders = list(orders_qs)
        # validate transitions
        to_process = []
        for o in orders:
            allowed = ALLOWED_TRANSITIONS.get(o.status, set())
            if new_status not in allowed:
                result['failed'].append(
                    {'order_id': o.id, 'error': 'INVALID_TRANSITION', 'from': o.status, 'to': new_status}
                )
            else:
                to_process.append(o)

        # group by trip id (None grouped separately)
        groups = defaultdict(list)
        for o in to_process:
            groups[o.trip_id].append(o)

        for trip_id, orders_group in groups.items():
            lock_key = (
                f"trip:{trip_id}:lock" if trip_id else f"orders:bulk:anon:{hash(tuple([o.id for o in orders_group]))}"
            )
            try:
                with redis_lock(lock_key, timeout=30):
                    with transaction.atomic():
                        # acquire DB locks
                        if trip_id:
                            TripDAO.get_trip_for_update(trip_id)
                        OrderDAO.lock_orders_for_update([o.id for o in orders_group])

                        # process each order
                        for order in orders_group:
                            handler_cls = HANDLER_MAP.get((order.status, new_status))
                            if handler_cls:
                                handler = handler_cls(order, ctx)
                                try:
                                    handler.run()
                                    result['success'].append(order.id)
                                except Exception as e:
                                    result['failed'].append({'order_id': order.id, 'error': str(e)})
                                    # policy: continue processing other orders in group
                            else:
                                # fallback: direct update + log
                                OrderDAO.update_status(order, new_status)
                                from orders.daos import OrderAssignmentLogDAO

                                OrderAssignmentLogDAO.create_log(
                                    order, actor_id, None, order.status, new_status, reason, {}
                                )
                                result['success'].append(order.id)
            except LockAcquireError:
                for order in orders_group:
                    result['failed'].append({'order_id': order.id, 'error': 'LOCK_ACQUIRE_FAILED'})
            except Exception as e:
                for order in orders_group:
                    result['failed'].append({'order_id': order.id, 'error': f'GROUP_ERROR: {str(e)}'})

        # After commit: enqueue side-effects
        changed_ids = result['success']
        if changed_ids:
            from orders.tasks import reindex_orders_task, send_order_status_notifications

            reindex_orders_task.delay(changed_ids)
            for oid in changed_ids:
                send_order_status_notifications.delay(oid, new_status, actor_id, reason)

        return {
            'success': result['success'],
            'failed': result['failed'],
            'context': {'created_trips': ctx.created_trips, 'redrops': ctx.redrops},
        }


## 5) File: `orders/tasks.py` (Celery hooks)


# orders/tasks.py
from celery import shared_task
from django.utils import timezone
from orders.daos import OrderDAO


@shared_task(bind=True, max_retries=3)
def reindex_orders_task(self, order_ids):
    try:
        # integrate with your existing ES bulk function
        from orders.elastic_search.tasks import bulk_reindex_orders

        bulk_reindex_orders(order_ids)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=3)
def send_order_status_notifications(self, order_id, new_status, actor_id=None, reason=None):
    # Minimal example; adapt to your notification stack
    from orders.models import Order

    order = Order.objects.filter(id=order_id).first()
    if not order:
        return
    payload = {
        'order_id': order.id,
        'new_status': new_status,
        'timestamp': timezone.now().isoformat(),
        'actor_id': actor_id,
        'reason': reason,
    }
    # webhooks, SMS, email, driver push
    try:
        from notifications.webhook import dispatch_order_webhook

        dispatch_order_webhook(payload)
    except Exception:
        pass

    try:
        from notifications.tasks import send_sms_to_recipient, send_email_to_recipient

        if getattr(order, 'recipient_phone', None):
            send_sms_to_recipient.delay(order.recipient_phone, f"Order #{order.id} status: {new_status}")
        if getattr(order, 'recipient_email', None):
            send_email_to_recipient.delay(
                order.recipient_email, "Order status changed", f"Order status changed to {new_status}"
            )
    except Exception:
        pass

    try:
        if getattr(order, 'driver', None):
            from drivers.notifications import push_to_driver

            push_to_driver(order.driver.id, payload)
    except Exception:
        pass


## 6)  Testing & Usage Notes
"""
1. **Add missing handlers:** The PDF defines many specific transitions. Implement a handler for each `(<from>, <to>)` pair and map it in `HANDLER_MAP`.
2. **Idempotency:** Make handlers idempotent — e.g., avoid creating duplicate redrops if handler retried.
3. **Lock strategy tuning:** Redis lock timeouts (`redis_lock`) and DB transaction time should be tuned to your workload. Acquire Redis lock *before* starting expensive work.
4. **Advisory locks alternate:** If you prefer to avoid Redis, you can use Postgres advisory locks inside DAOs before heavy prep work. But advisory locks are process-scoped and require careful cleanup.
5. **Testing concurrency:** Simulate concurrent updates: driver automated updates vs admin manual changes to ensure correct behavior.
6. **Observability:** Instrument lock acquisition timeouts, handler runtimes, and failure rates.
"""

## 7) Next steps I can take for you
"""
- Expand the handler set to cover every transition in the PDF and include unit tests.
- Convert Redis locks to Postgres advisory locks and show a comparison.
- Create integration tests that spin up transactions and simulate concurrency.
- Wire this into your current TripBuilder implementation (copy/paste TripBuilder if you want me to adapt directly).
"""
