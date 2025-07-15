from rest_framework import serializers
from dispatch.models import TripStop, Location


class LocationMinimSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'latitude', 'longitude']
        ref_name = 'trip_stops'

    def get_latitude(self, obj):
        return obj.coordinates.y

    def get_longitude(self, obj):
        return obj.coordinates.x


class TripStopListSerializer(serializers.ModelSerializer):
    location = LocationMinimSerializer()

    class Meta:
        model = TripStop
        fields = [
            'id',
            'created_at',
            'updated_at',
            'completed_at',
            'notes',
            'stop_type',
            'sequence',
            'estimated_duration',
            'order',
            'driver_profile',
            'trip',
            'location',
            'completed',
        ]


class TripStopCompletionSerializer(serializers.Serializer):
    """
    Serializer for completing trip stops
    """

    pass
