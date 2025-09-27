from django.db import transaction
from django.utils.crypto import get_random_string

from organisations.models import Organisation, OrganisationConfiguration
from django.contrib.auth import get_user_model


class OrganisationRegistrationService:
    @staticmethod
    @transaction.atomic
    def register_organisation(**org_data):
        # Create organisation
        org = Organisation.objects.create(**org_data)
        email = org_data.get('email')
        first_name = org_data.get('name')

        # Create first user
        user_model = get_user_model()
        user = user_model.objects.create_user(
            email=email,
            organisation=org,
            first_name=first_name,
            last_name='Admin',
        )
        pwd = get_random_string(length=10)
        user.set_password(pwd)
        user.save()
        # TODO: Send email with credentials

        # Create initial org configurations
        OrganisationConfiguration.objects.create(organisation=org)
        return org, user


class OrganisationUpdateService:
    @staticmethod
    @transaction.atomic
    def update_organisation(*, organisation: Organisation, **updates):
        for field, value in updates.items():
            setattr(organisation, field, value)
        organisation.save(update_fields=list(updates.keys()))
        return organisation