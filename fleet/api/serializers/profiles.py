from rest_framework import serializers
from fleet.models import DriverProfile, Vehicle, DriverGroup
from users.models import Driver


class DriverMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', 'email', 'is_active', 'last_login']
        ref_name = 'profiles'


class VehicleMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'registration_number']
        ref_name = 'profiles'


class DriverGroupMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverGroup
        fields = ['id', 'name']
        ref_name = 'profiles'


class DriverProfileListSerializer(serializers.ModelSerializer):
    driver = DriverMinimSerializer()
    vehicle = VehicleMinimSerializer()
    driver_group = DriverGroupMinimSerializer()

    class Meta:
        model = DriverProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'driver',
            'status',
            'active',
            'vehicle',
            'driver_group',
            'created_at',
        ]
        ref_name = 'profiles'


class ProfileActionSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=1000, required=False, allow_null=True)
