from rest_framework import serializers

from organisations.models import OrganisationSubscription


class OrganisationSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationSubscription
        fields = '__all__'
        read_only_fields = ['payment_reference']
