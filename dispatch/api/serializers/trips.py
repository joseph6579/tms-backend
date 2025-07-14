from rest_framework import serializers
from dispatch.models import Trip, TripStop
from dispatch.api.serializers.orders import OrderSerializer
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


class TripCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'
