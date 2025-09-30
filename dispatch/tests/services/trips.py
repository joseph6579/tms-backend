import pytest

from dispatch.models import Order, TripStop
from dispatch.services.trip_service import TripBuilder


@pytest.fixture
def factory_order(db):
    def create(**kwargs):
        return Order.objects.create(reference_number="ORD-001", status="scheduled", **kwargs)

    return create


@pytest.fixture
def factory_organisation(db):
    def create(**kwargs):
        from organisations.models import Organisation

        return Organisation.objects.create(name="TestOrg", **kwargs)

    return create


@pytest.fixture
def factory_driver_profile(db):
    def create(**kwargs):
        from fleet.models import DriverProfile

        return DriverProfile.objects.create(first_name="Jane", last_name="Doe", status="available", **kwargs)

    return create


@pytest.mark.django_db
def test_trip_builder_creates_trip_and_stops(factory_organisation, factory_order, factory_driver_profile):
    org = factory_organisation()
    driver = factory_driver_profile(organisation=org)

    order1 = factory_order(organisation=org)
    order2 = factory_order(organisation=org)

    orders_data = [
        {
            "id": str(order1.id),
            "origin": {"name": "Pickup A", "latitude": -1.1, "longitude": 36.8},
            "drop_off": {"name": "Drop A", "latitude": -1.2, "longitude": 36.9},
        },
        {
            "id": str(order2.id),
            "origin": {"name": "Pickup B", "latitude": -1.3, "longitude": 36.7},
            "drop_off": {"name": "Drop B", "latitude": -1.4, "longitude": 36.6},
        },
    ]

    start_location = {"name": "Start Yard", "latitude": -1.0, "longitude": 36.5}
    end_location = {"name": "End Yard", "latitude": -1.5, "longitude": 36.4}

    builder = TripBuilder(
        organisation=org,
        driver_profile=driver,
        orders_data=orders_data,
        start_loc_data=start_location,
        end_loc_data=end_location,
    )

    trip = builder.build()

    # Verify trip
    assert trip.organisation == org
    assert trip.driver_profile == driver
    assert trip.vehicle == driver.vehicle
    assert trip.start_location.name == "Start Yard"
    assert trip.end_location.name == "End Yard"
    assert trip.status == "assigned"

    # Verify orders were updated
    order1.refresh_from_db()
    order2.refresh_from_db()
    assert order1.trip_id == trip.id
    assert order1.driver_profile_id == driver.id
    assert order1.status == "assigned"

    # Verify trip stops
    stops = TripStop.objects.filter(trip=trip).order_by("sequence")
    stop_types = [s.stop_type for s in stops]
    expected_types = [
        "start",  # trip start
        "at_store",
        "pickup",
        "at_drop_off",
        "drop_off",  # order1
        "at_store",
        "pickup",
        "at_drop_off",
        "drop_off",  # order2
        "end",  # trip end
    ]
    assert stop_types == expected_types
    assert stops.first().location.name == "Start Yard"
    assert stops.last().location.name == "End Yard"

    # Check that stops are associated with correct orders
    order_stop_ids = [s.order_id for s in stops if s.order_id]
    assert set(order_stop_ids) == {order1.id, order2.id}


@pytest.mark.django_db
def test_trip_builder_without_driver(factory_organisation, factory_order):
    org = factory_organisation()

    order1 = factory_order(organisation=org)
    order2 = factory_order(organisation=org)

    orders_data = [
        {
            "id": str(order1.id),
            "origin": {"name": "Pickup A", "latitude": -1.1, "longitude": 36.8},
            "drop_off": {"name": "Drop A", "latitude": -1.2, "longitude": 36.9},
        },
        {
            "id": str(order2.id),
            "origin": {"name": "Pickup B", "latitude": -1.3, "longitude": 36.7},
            "drop_off": {"name": "Drop B", "latitude": -1.4, "longitude": 36.6},
        },
    ]

    start_location = {"name": "Dispatch Base", "latitude": -1.0, "longitude": 36.5}

    builder = TripBuilder(
        organisation=org,
        orders_data=orders_data,
        start_loc_data=start_location,
        driver_profile=None,  # 🔑 No driver assigned
        end_loc_data=None,
    )

    trip = builder.build()

    # Verify trip
    assert trip.organisation == org
    assert trip.driver_profile is None
    assert trip.vehicle is None
    assert trip.start_location.name == "Dispatch Base"
    assert trip.end_location is None
    assert trip.status == "pending"

    # Verify orders updated
    order1.refresh_from_db()
    order2.refresh_from_db()
    assert order1.status == "broadcasted"
    assert order1.trip_id == trip.id
    assert order1.driver_profile_id is None

    # Verify trip stops
    stops = TripStop.objects.filter(trip=trip).order_by("sequence")
    stop_types = [s.stop_type for s in stops]
    expected_types = [
        "start",
        "at_store",
        "pickup",
        "at_drop_off",
        "drop_off",
        "at_store",
        "pickup",
        "at_drop_off",
        "drop_off",
        "end",
    ]
    assert stop_types == expected_types
    assert stops.first().location.name == "Dispatch Base"
    assert stops.last().location.name == "Dispatch Base"
