from rest_framework import serializers
from organisations.models import Store
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string


class LocationWrite(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({key: 'This field is required' for key in self.fields.keys()})
        extra_fields = set(data.keys()) - set(self.fields.keys())
        if extra_fields:
            raise serializers.ValidationError({key: 'This field is not allowed' for key in extra_fields})
        return super().to_internal_value(data)


class StoreWriteSerializer(serializers.ModelSerializer):
    location = LocationWrite()

    class Meta:
        model = Store
        fields = ['name', 'key', 'location', 'broadcast_radius']

    def _get_organisation(self):
        user = self.context['request'].user
        return user.organisation if user else None

    def validate_name(self, value):
        value = value.lower()
        org = self._get_organisation()
        org_id = getattr(org, 'id')
        qs = Store.objects.only('id', 'name', 'organisation_id').filter(name=value, organisation_id=org_id)
        if instance := self.instance:
            qs = qs.exclude(id=instance.id)
        if qs.exists():
            raise serializers.ValidationError(_('store with this name exists'))
        return value

    def validate_key(self, value):
        instance = self.instance
        value = value or (instance.key if instance and instance.key else get_random_string(32))
        value = ''.join(value.split())
        org = self._get_organisation()
        org_id = getattr(org, 'id')
        qs = Store.objects.only('id', 'key', 'organisation_id').filter(key=value, organisation_id=org_id)
        if instance:
            qs = qs.exclude(id=instance.id)
        if qs.exists():
            raise serializers.ValidationError(_('store with this key exists'))
        return value

    def validate(self, attrs):
        key = attrs.get('key', None)
        if not key:
            attrs['key'] = self.validate_key(key)
        return super().validate(attrs)


class StoreModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'name', 'key', 'location', 'broadcast_radius', 'organisation_id']
