from rest_framework import serializers
from fleet.models import DriverProfile, Vehicle, DriverGroup
from users.models import Driver


class DriverMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', 'email', 'is_active']
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
