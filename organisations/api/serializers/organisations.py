from django.contrib.auth import get_user_model
from rest_framework import serializers
from pydantic import ValidationError


class OrganisationRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()

    def validate_email(self, value):
        user_model = get_user_model()
        if user_model.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class OrganisationRedactedSerializer(serializers.ModelSerializer):
    configuration_id = serializers.UUIDField(source='configuration.id', read_only=True)

    class Meta:
        from organisations.models import Organisation  # Avoid circular import

        model = Organisation
        fields = ['id', 'name', 'email', 'phone_number', 'created_at', 'updated_at', 'configuration_id']


class OrganisationUpdateSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()


class OrganisationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        from organisations.models import Organisation

        model = Organisation
        fields = '__all__'


class OrganisationOrderConfigurationSerializer(serializers.Serializer):
    config = serializers.JSONField()

    def validate_config(self, value):
        from commons.constants import OrderStatusConfiguration

        try:
            OrderStatusConfiguration.model_validate(value)
        except ValidationError as e:
            err_dict = e.errors()
            msg = err_dict[0]['ctx']['error'] if 'ctx' in err_dict[0] else 'Invalid configuration'
            raise serializers.ValidationError(msg)
        except Exception as e:
            print(type(e))
            raise serializers.ValidationError(str(e))
        return value
