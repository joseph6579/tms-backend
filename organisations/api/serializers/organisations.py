from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework import serializers

from organisations.models import Organisation, Package, OrganisationSubscription, OrganisationPreferences

User = get_user_model()

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'

class OrganisationSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationSubscription
        fields = '__all__'
        read_only_fields = ['payment_reference']

class OrganisationPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationPreferences
        fields = '__all__'

class OrganisationSerializer(serializers.ModelSerializer):
    preferences = OrganisationPreferencesSerializer(read_only=True)
    active_subscription = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = '__all__'

    def get_active_subscription(self, obj):
        subscription = obj.subscriptions.filter(is_active=True).first()
        if subscription:
            return OrganisationSubscriptionSerializer(subscription).data
        return None

    def create(self, validated_data):
        email = validated_data.get('email')
        user = None
        try:
            user = User.objects.get(email=email)
            if user:
                raise serializers.ValidationError('User with email already exists')
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                first_name=validated_data.get('name'),
                last_name='Admin'
            )
            organisation = Organisation.objects.create(**validated_data)
            
            # Create default preferences
            OrganisationPreferences.objects.create(organisation=organisation)
            
            pwd = get_random_string(length=10)
            user.set_password(pwd)
            user.organisation = organisation
            user.save()
            # TODO: Send email with credentials
        return organisation