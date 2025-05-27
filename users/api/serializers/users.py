from django.contrib.auth import get_user_model
from rest_framework import serializers

from organisations.models import Organisation
from users.models import Driver

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

class GoogleResponseSerializer(serializers.Serializer):
    """
    Serializer for Google Response
    """
    code = serializers.CharField(required=True)