from django.contrib.auth import get_user_model
from rest_framework import serializers

from organisations.models import Organisation
from users.models import Driver
from dispatch.models import Order, Location

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False, allow_null=False)
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'organisation', 'role', 'organisation']
        ref_name = 'Users'
        required_fields = ['email', 'first_name', 'last_name', 'organisation']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        ref_name = 'Users'
        required_fields = ['email', 'first_name', 'last_name', 'organisation']

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']
        ref_name = 'Users'

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'

class DriverLocationUpdateSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

class LocationMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'city']

class DeliveryHistorySerializer(serializers.ModelSerializer):
    pickup_details = LocationMiniSerializer(source='pickup', read_only=True)
    drop_off_details = LocationMiniSerializer(source='drop_off', read_only=True)
    earnings = serializers.DecimalField(max_digits=10, decimal_places=2, source='payment_amount', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'reference', 'status', 'pickup_details', 'drop_off_details',
            'created_at', 'date_delivered', 'earnings', 'description'
        ]

class DriverEarningsSerializer(serializers.Serializer):
    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_bonus = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_deductions = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_count = serializers.IntegerField()
    completed_deliveries = serializers.IntegerField()

class GoogleResponseSerializer(serializers.Serializer):
    """
    Serializer for Google Response
    """
    code = serializers.CharField(required=True)