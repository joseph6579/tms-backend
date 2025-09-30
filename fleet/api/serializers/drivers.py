from django.contrib.auth import get_user_model
from rest_framework import serializers

from dispatch.models import Location, Order
from users.models import Driver
from fleet.models import (
    Vehicle,
    DriverGroup,
    DriverProfile,
    VEHICLE_TYPES,
    VEHICLE_SOURCES,
)
from django.utils.translation import gettext_lazy as _


class DriverRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    national_id = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15)
    vehicle_registration_number = serializers.CharField(max_length=20)
    vehicle_type = serializers.ChoiceField(choices=VEHICLE_TYPES)
    vehicle_source = serializers.ChoiceField(choices=VEHICLE_SOURCES)
    vehicle_capacity = serializers.DecimalField(max_digits=10, decimal_places=2)
    driver_group = serializers.PrimaryKeyRelatedField(
        queryset=DriverGroup.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Driver
        fields = [
            "first_name",
            "last_name",
            "national_id",
            "email",
            "phone_number",
            "vehicle_registration_number",
            "vehicle_type",
            "vehicle_capacity",
            "vehicle_source",
            "driver_group",
        ]

    def _get_organisation(self):
        user = self.context["request"].user
        return user.organisation if user else None

    def validate_first_name(self, value):
        return ''.join(value.split()).lower()

    def validate_last_name(self, value):
        return ''.join(value.split()).lower()

    def validate_driver_group(self, value):
        if value is None:
            return value
        organisation = self._get_organisation()
        if (
            not DriverGroup.objects.only("id", "organisation_id")
            .filter(id=value, organisation_id=organisation.id)
            .exists()
        ):
            raise serializers.ValidationError(_("invalid choice"))
        return value

    def validate_vehicle_registration_number(self, value):
        value = ''.join(value.split()).lower()
        organisation = self._get_organisation()
        if (
            Vehicle.objects.only("registration_number", "organisation_id")
            .filter(registration_number=value, organisation_id=organisation.id)
            .exists()
        ):
            raise serializers.ValidationError(_("registration number already exists"))
        return value

    def validate_national_id(self, value):
        value = value.strip().lower()
        organisation = self._get_organisation()
        if (
            DriverProfile.objects.only("id", "national_id", "organisation_id")
            .filter(national_id=value, organisation_id=organisation.id)
            .exists()
        ):
            raise serializers.ValidationError(_("driver with this national ID already exists"))
        return value

    def validate_email(self, value):
        """
        if the email belongs to a user who is not a driver raise an error
        If the email belongs to driver in the same organisation raise an error
        :param value:
        :return:
        """
        value = value.lower()
        organisation = self._get_organisation()
        user = get_user_model()
        if (
            user.objects.only("email", "organisation_id", "role")
            .filter(email=value, organisation_id=organisation.id)
            .exclude(role="driver")
            .exists()
        ):
            raise serializers.ValidationError(_("staff with this email exists"))
        if driver := Driver.objects.only("id", "email").filter(email=value).first():
            if (
                DriverProfile.objects.only("id", "driver_id", "organisation_id")
                .filter(driver_id=driver.id, organisation_id=organisation)
                .exists()
            ):
                raise serializers.ValidationError(_("driver with this email exists"))
        return value

    def validate_phone_number(self, value):
        """
        If the phone number belongs to driver in the same organisation raise an error
        :param value:
        :return:
        """
        value = ''.join(value.split())
        organisation = self._get_organisation()
        if driver := Driver.objects.only("id", "phone_number").filter(phone_number=value).first():
            if (
                DriverProfile.objects.only("id", "driver_id", "organisation_id")
                .filter(driver_id=driver.id, organisation_id=organisation)
                .exists()
            ):
                raise serializers.ValidationError(_("driver with this phone number exists"))
        return value


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
            'id',
            'reference',
            'status',
            'pickup_details',
            'drop_off_details',
            'created_at',
            'date_delivered',
            'earnings',
            'description',
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
