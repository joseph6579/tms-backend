from rest_framework import serializers
from dispatch.models import Trip, TripStop
from dispatch.api.serializers.orders import OrderSerializer
from users.api.serializers.users import UserMiniSerializer

class TripStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripStop
        fields = '__all__'

class TripSerializer(serializers.ModelSerializer):
    stops = TripStopSerializer(many=True, read_only=True)
    orders = OrderSerializer(many=True, read_only=True)
    driver_details = UserMiniSerializer(source='driver', read_only=True)

    class Meta:
        model = Trip
        fields = '__all__'