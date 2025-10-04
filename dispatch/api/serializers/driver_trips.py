from rest_framework import serializers

from dispatch.models import Trip, TripStop, Location, Order
from organisations.models import Customer, Store


class CoordinatesSerializer(serializers.Serializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        fields = ['latitude', 'longitude']
        ref_name = 'driver_trips'

    def get_latitude(self, obj):
        return obj.y

    def get_longitude(self, obj):
        return obj.x


class LocationSerializer(serializers.ModelSerializer):
    coordinates = CoordinatesSerializer()

    class Meta:
        model = Location
        fields = ['id', 'address', 'coordinates', 'name']
        ref_name = 'driver_trip_locations'


class CustomerMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone_number']
        ref_name = 'driver_trip_customers'


class StoreMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            'id',
            'name',
        ]
        ref_name = 'driver_trip_stores'


class OrderMinimSerializer(serializers.ModelSerializer):
    pickup = LocationSerializer()
    drop_off = LocationSerializer()
    buyer = CustomerMinimSerializer()
    recipient = CustomerMinimSerializer()
    store = StoreMinimSerializer()

    class Meta:
        from dispatch.services.driver_trips import driver_trips_svc

        model = Order
        fields = driver_trips_svc.order_fields() + ['pickup', 'drop_off', 'buyer', 'recipient', 'store']
        ref_name = 'driver_trip_orders'


class DriverTripStopSerializer(serializers.ModelSerializer):
    coordinates = CoordinatesSerializer()

    class Meta:
        from dispatch.services.driver_trips import driver_trips_svc

        model = TripStop
        fields = driver_trips_svc.trip_stop_fields()
        ref_name = 'driver_trip_stops'


class DriverTripListSerializer(serializers.ModelSerializer):
    start_point = CoordinatesSerializer()
    end_point = CoordinatesSerializer()
    stops = DriverTripStopSerializer(many=True, read_only=True)
    orders = OrderMinimSerializer(many=True, read_only=True)

    class Meta:
        from dispatch.services.driver_trips import driver_trips_svc

        model = Trip
        fields = driver_trips_svc.trip_fields() + ['stops', 'orders']
        ref_name = 'driver_trips'
