from rest_framework import serializers
from fleet.models import Vehicle, DriverProfile
from django.utils.translation import gettext_lazy as _


class DriverProfileMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = ['id', 'first_name', 'last_name', 'driver_id']
        ref_name = 'vehicles'


class VehicleListSerializer(serializers.ModelSerializer):
    driver = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id',
            'registration_number',
            'created_at',
            'updated_at',
            'vehicle_type',
            'source',
            'capacity',
            'driver',
        ]

    def get_driver(self, obj):
        if hasattr(obj, 'driver_profile_obj'):
            return DriverProfileMinimSerializer(obj.driver_profile_obj[0]).data


class VehicleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['registration_number', 'vehicle_type', 'source', 'capacity']

    def _get_organisation(self):
        user = self.context['request'].user
        return user.organisation if user else None

    def validate_registration_number(self, value):
        org = self._get_organisation()
        organisation_id = getattr(org, 'organisation_id')
        value = ''.join(value.split().lower())
        qs = Vehicle.objects.only('id', 'registration_number', 'organisation_id').filter(
            registration_number=value, organisation_id=organisation_id
        )
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(_('vehicle with this registration number exists'))
        return value


class AssignVehicleSerializer(serializers.Serializer):
    profile_id = serializers.PrimaryKeyRelatedField(queryset=DriverProfile.objects.all())
