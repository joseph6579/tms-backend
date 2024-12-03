from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework import serializers

from organisations.models import Organisation

"""
1. Check if email exists
2. Check if user with the email already exists
3. Create User and send email with credentials
4. Create Organisation
"""
User = get_user_model()

class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = '__all__'

    def create(self, validated_data):
        email = validated_data.get('email')
        user = None
        try:
            user = User.objects.get(email=email)
            if user:
                raise serializers.ValidationError('User with email already exists')
        except User.DoesNotExist:
            user = User.objects.create_user(email=email, password='password')
            organisation = Organisation.objects.create(**validated_data)
            pwd = get_random_string(length=10)
            user.set_password(pwd)
            user.organisation = organisation
            user.save()
            # TODO: Send email with credentials
        return organisation