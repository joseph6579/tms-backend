from rest_framework import serializers
from dispatch.models import Order, Location, Customer
from users.api.serializers.users import UserMiniSerializer

class LocationMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'city']

class CustomerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone_number']

class OrderSerializer(serializers.ModelSerializer):
    pickup_details = LocationMiniSerializer(source='pickup', read_only=True)
    drop_off_details = LocationMiniSerializer(source='drop_off', read_only=True)
    recipient_details = CustomerMiniSerializer(source='recipient', read_only=True)
    buyer_details = CustomerMiniSerializer(source='buyer', read_only=True)
    driver_details = UserMiniSerializer(source='driver', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set organization from request user
        validated_data['organization'] = self.context['request'].user.organisation
        return super().create(validated_data)