from rest_framework import serializers
from fleet.models import DriverProfile


class DriverProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = '__all__'
