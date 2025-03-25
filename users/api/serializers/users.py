from django.contrib.auth import get_user_model
from rest_framework import serializers

from organisations.models import Organisation

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


class GoogleResponseSerializer(serializers.Serializer):
    """
    Serializer for Google Response
    """
    code = serializers.CharField(required=True, max_length=500)