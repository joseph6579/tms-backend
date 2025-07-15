from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from dispatch.constants import OrderStatusChoices
from dispatch.models import Trip, TripStop, Order, Location
from dispatch.api.serializers.orders_old import OrderSerializer
from fleet.models import DriverProfile, Vehicle
from users.api.serializers.users import UserMiniSerializer


class TripStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripStop
        fields = '__all__'
        read_only_fields = ['completed_by']

    def validate(self, data):
        if data.get('status') == 'completed' and not data.get('completed_at'):
            raise serializers.ValidationError("completed_at is required when status is completed")
        return data


class TripSerializer(serializers.ModelSerializer):
    stops = TripStopSerializer(many=True, read_only=True)
    orders = OrderSerializer(many=True, read_only=True)
    driver_details = UserMiniSerializer(source='driver', read_only=True)

    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        if data.get('status') == 'completed' and not data.get('completed_time'):
            raise serializers.ValidationError("completed_time is required when status is completed")
        return data


class LocationMinimSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'latitude', 'longitude']
        ref_name = 'trips'

    def get_latitude(self, obj):
        return obj.coordinates.y

    def get_longitude(self, obj):
        return obj.coordinates.x


class DriverProfileMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = [
            'id',
            'first_name',
            'last_name',
        ]
        ref_name = 'trips'


class VehicleMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'registration_number']


class TripListSerializer(serializers.ModelSerializer):
    start_location = LocationMinimSerializer()
    end_location = LocationMinimSerializer()
    driver_profile = DriverProfileMinimSerializer()
    vehicle = VehicleMinimSerializer()

    class Meta:
        model = Trip
        # fields = '__all__'
        fields = [
            'id',
            'created_at',
            'updated_at',
            'status',
            'completed_time',
            'estimated_duration',
            'actual_duration',
            'planned_geometry',
            'actual_geometry',
            'notes',
            'distance',
            'driver_profile',
            'vehicle',
            'start_location',
            'end_location',
        ]


class LocationForTrip(serializers.Serializer):
    name = serializers.CharField(max_length=1000)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class OrderForTripSerializer(serializers.Serializer):
    # id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    id = serializers.UUIDField()
    origin = LocationForTrip()
    drop_off = LocationForTrip()


class BasicTripCreationSerializer(serializers.Serializer):
    """
    Serializer used to create non optimized Trips.
    1. Orders - a list of orders
    2. Driver Profile
    """

    # orders = serializers.ListSerializer(
    #     child=serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    # )
    orders = serializers.ListSerializer(child=OrderForTripSerializer(), allow_empty=False, allow_null=False)
    driver_profile = serializers.PrimaryKeyRelatedField(queryset=DriverProfile.objects.all())
    start_location = LocationForTrip()
    end_location = LocationForTrip()  # Should be the last point of the trip

    def _get_user(self):
        return self.context['request'].user

    def _get_organisation(self):
        user = self._get_user()
        return user.organisation_id if user else None

    def validate_orders(self, values):
        """
        1. Check if all orders are from the same organisation
        2. Check if all orders are in a non-assigned status
        :param values:
        :return: raise a validation error or return the validated values
        """
        org_id = self._get_organisation()
        order_ids = [order.get('id') for order in values]
        allowed_statuses = OrderStatusChoices.unassigned_statuses()
        rows = Order.objects.filter(id__in=order_ids).values_list('organisation_id', 'status')
        org_ids = set()
        invalid_status_found = False

        for org, status in rows:
            org_ids.add(org)
            if status not in allowed_statuses:
                invalid_status_found = True
                break

        if len(org_ids) != 1 or org_id not in org_ids:
            raise serializers.ValidationError(_("Orders do not all belong to the current organisation"))

        if invalid_status_found:
            raise serializers.ValidationError(_("Some orders have an invalid status"))
        return values

    def validate_driver_profile(self, value):
        if value.organisation_id != self._get_organisation():
            raise serializers.ValidationError(_('Incorrect driver data'))
        return value
