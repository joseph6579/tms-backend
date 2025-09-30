from django.contrib.gis.geos import Point
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from dispatch.models import Location
from organisations.api.serializers.stores import LocationWrite
from organisations.models import Customer


class CustomerModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class LocationMinimSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Location
        geo_field = 'coordinates'
        fields = ['id', 'name', 'latitude', 'longitude']

    def get_latitude(self, obj):
        return obj.coordinates.y

    def get_longitude(self, obj):
        return obj.coordinates.x


class CustomerListSerializer(serializers.ModelSerializer):
    location = LocationMinimSerializer()

    class Meta:
        model = Customer
        fields = ['id', 'organisation_id', 'name', 'email', 'phone_number', 'is_active', 'location']


class CustomerWriteSerializer(serializers.ModelSerializer):
    location = LocationWrite(required=False)

    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number', 'location', 'notes']

    def validate(self, attrs):
        instance = self.instance
        phone_number = attrs.get('phone_number', None) or (instance.phone_number if instance else None)
        email = attrs.get('email', None) or (instance.email if instance else None)
        if phone_number is None and email is None:
            raise serializers.ValidationError({'detail': _('provide a phone number or an email address')})
        return super().validate(attrs)

    def validate_location(self, value):
        instance = self.instance
        value = value or (instance.location if instance else None)
        if value:
            if isinstance(value, dict):
                # get or create location object
                point = Point(value.get('longitude'), value.get('latitude'))
                value, created = Location.objects.only('id').get_or_create(
                    defaults={'name': value.get('name'), 'address': value.get('name'), 'coordinates': point}
                )
        return value
