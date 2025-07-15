import uuid

from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from dispatch.models import Order, Location
from fleet.models import DriverProfile
from organisations.api.serializers.stores import LocationWrite
from organisations.models import Store, Customer


class OrderDimensionsSerializer(serializers.Serializer):
    length = serializers.DecimalField(max_digits=10, decimal_places=4)
    width = serializers.DecimalField(max_digits=10, decimal_places=4)
    height = serializers.DecimalField(max_digits=10, decimal_places=4)

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({key: _('This field is required') for key in self.fields.keys()})
        extra_fields = set(data.keys()) - set(self.fields.keys())
        if extra_fields:
            raise serializers.ValidationError({key: _('this field is not allowed') for key in extra_fields})
        return super().to_internal_value(data)


class OrderWriteSerializer(serializers.ModelSerializer):
    pickup = LocationWrite()
    drop_off = LocationWrite()
    store_key = serializers.CharField(max_length=100, allow_null=True, required=False)

    # customer details TODO: Validate required fields
    recipient_name = serializers.CharField(max_length=50)
    recipient_phone_number = serializers.CharField(max_length=20, required=False, allow_null=True)
    recipient_email = serializers.EmailField(required=False, allow_null=True)

    buyer_name = serializers.CharField(max_length=50, required=False, allow_null=True)
    buyer_phone_number = serializers.CharField(max_length=20, required=False, allow_null=True)
    buyer_email = serializers.EmailField(required=False, allow_null=True)

    # measurements
    weight = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True, required=False)
    dimensions = OrderDimensionsSerializer(required=False)

    class Meta:
        model = Order
        fields = [
            'reference_number',
            'pickup',
            'drop_off',
            'description',
            'instructions',
            'priority',
            'buyer_name',
            'buyer_email',
            'buyer_phone_number',
            'recipient_name',
            'recipient_phone_number',
            'recipient_email',
            'store_key',
            'weight',
            'dimensions',
        ]
        extra_kwargs = {
            'store': {'read_only': True},
            'organisation': {'read_only': True},
        }

    @staticmethod
    def _customer_validation(phone: str = None, email: str = None, field: str = 'recipient'):
        if phone is None and email is None:
            raise serializers.ValidationError({'detail': _(f'include either {field} phone number or {field} email')})

    @staticmethod
    def _get_or_create_customer(name: str, loc_id: uuid, org_id: str, phone: str = None, email: str = None) -> Customer:
        lookup = {}
        if phone:
            lookup['phone_number'] = phone
        elif email:
            lookup['email'] = email
        else:
            raise ValueError("Either phone or email must be provided")

        lookup['organisation_id'] = org_id

        try:
            customer, created = Customer.objects.only('id').get_or_create(
                defaults={
                    'name': name,
                    'location_id': loc_id,
                    'email': email,
                    'phone_number': phone,
                },
                **lookup,
            )

            # If customer exists but name/email/location changed, optionally update
            updated = False
            if not created:
                if name and customer.name != name:
                    customer.name = name
                    updated = True
                if loc_id != customer.location_id:
                    customer.location_id = loc_id
                if updated:
                    customer.save(update_fields=['name', 'location_id'])
            return customer

        except MultipleObjectsReturned:
            customer = Customer.objects.filter(**lookup).first()
            return customer

    def _get_or_create_location(self, name: str, lat: float, lon: float) -> Location:
        point = Point(lon, lat)
        loc, _ = Location.objects.get_or_create(defaults={'name': name, 'coordinates': point})
        return loc

    def _validate_location(self, data, field):
        if isinstance(data, dict):
            name = data.get('name')
            lon = data.get('longitude')
            lat = data.get('latitude')
            point = Point(float(lon), float(lat))
            location, _ = Location.objects.only('id').get_or_create(
                name=name, coordinates=point, defaults={'address': name}
            )
            return location
        raise serializers.ValidationError(_(f'{field} location is required'))

    def validate(self, attrs):
        # validate locations
        org = self._get_organisation()
        pickup = attrs.pop('pickup')
        drop_off = attrs.pop('drop_off')
        attrs['pickup'] = pickup
        attrs['drop_off'] = drop_off

        # validate recipient
        self._customer_validation(phone=attrs['recipient_phone_number'], email=attrs['recipient_email'])
        recipient = self._get_or_create_customer(
            name=attrs.pop('recipient_name'),
            email=attrs.pop('recipient_email', None),
            phone=attrs.pop('recipient_phone_number', None),
            loc_id=drop_off.id,
            org_id=org.id,
        )
        attrs['recipient'] = recipient
        # validate buyer
        buyer_name = attrs.pop('buyer_name', None)
        if buyer_name:
            self._customer_validation(phone=attrs['buyer_phone_number'], email=attrs['buyer_email'], field='buyer')
            buyer = self._get_or_create_customer(
                name=attrs.pop('buyer_name'),
                email=attrs.pop('buyer_email', None),
                phone=attrs.pop('buyer_phone_number', None),
                loc_id=drop_off.id,
                org_id=org.id,
            )
            attrs['buyer'] = buyer
        # update store value
        attrs['store'] = attrs.pop('store_key', None)
        return super().validate(attrs)

    def _get_organisation(self):
        user = self.context['request'].user
        return user.organisation if user else None

    def validate_reference_number(self, value):
        instance = self.instance
        org = self._get_organisation()
        value = value or (instance.reference_number if instance else get_random_string(12))
        qs = Order.objects.only('id', 'reference_number', 'organisation_id').filter(
            reference_number=value, organisation_id=org.id
        )
        if instance:
            qs = qs.exclude(id=instance.id)
        if qs.exists():
            raise serializers.ValidationError(_('order with this reference number exists'))
        return value

    def validate_store_key(self, value):
        if value:
            org = self._get_organisation()
            store = Store.objects.only('id', 'organisation_id').filter(key=value, organisation_id=org.id).first()
            if not store:
                raise serializers.ValidationError(_('Invalid store key'))
            return store
        return None

    def validate_pickup(self, value):
        return self._validate_location(data=value, field='pickup')

    def validate_drop_off(self, value):
        return self._validate_location(data=value, field='drop_off')


class LocationMinimSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'latitude', 'longitude']
        ref_name = 'orders'

    def get_latitude(self, obj):
        return obj.coordinates.y

    def get_longitude(self, obj):
        return obj.coordinates.x


class RecipientMinimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone_number', 'email']
        ref_name = 'orders'


class DriverProfileMinimSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = DriverProfile
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email']
        ref_name = 'orders'

    def get_phone_number(self, obj):
        return obj.driver.phone_number

    def get_email(self, obj):
        return obj.driver.email


class OrderListSerializer(serializers.ModelSerializer):
    pickup = LocationMinimSerializer()
    drop_off = LocationMinimSerializer()
    recipient = RecipientMinimSerializer()
    driver_profile = DriverProfileMinimSerializer()

    class Meta:
        model = Order
        # fields = '__all__'
        fields = [
            'id',
            'created_at',
            'updated_at',
            'reference_number',
            'status',
            'priority',
            'date_delivered',
            'date_cancelled',
            'date_failed',
            'description',
            'instructions',
            'store',
            'driver_profile',
            'recipient',
            'buyer',
            'pickup',
            'drop_off',
        ]
