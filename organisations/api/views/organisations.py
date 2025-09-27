from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from organisations.api.serializers.organisations import OrganisationRegistrationSerializer, \
    OrganisationRedactedSerializer, OrganisationUpdateSerializer, OrganisationOrderConfigurationSerializer
from organisations.models import Organisation, OrganisationConfiguration
from organisations.permissions import IsMasterUserOrReadOnly
from organisations.services.organisation_configuration import OrganisationConfigService

from organisations.services.organization_management import OrganisationUpdateService, OrganisationRegistrationService


class OrganisationViewSet(ReadOnlyModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationRegistrationSerializer
    permission_classes = [IsMasterUserOrReadOnly]


    def get_serializer_class(self):
        serializers = {
            'retrieve': OrganisationRedactedSerializer
        }
        return serializers.get(self.action, self.serializer_class)



    @action(detail=False, methods=["post"], url_path='register')
    def register(self, request, *args, **kwargs):
        serializer = OrganisationRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org, _ = OrganisationRegistrationService.register_organisation(**serializer.validated_data)
        org_data = OrganisationRedactedSerializer(instance=org).data
        return Response(org_data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=["put"], url_path='update-details', serializer_class=OrganisationUpdateSerializer)
    def update_details(self, request, *args, **kwargs):
        org = self.get_object()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_org = OrganisationUpdateService.update_organisation(organisation=org, **serializer.validated_data)

        org_data = OrganisationRedactedSerializer(instance=updated_org).data
        return Response(org_data, status=status.HTTP_200_OK)


    @action(detail=True, methods=["get"], url_path='order-status-configuration')
    def read_configuration(self, request, *args, **kwargs):
        org = self.get_object()
        config = org.configuration.order_status_configuration
        return Response(config, status=status.HTTP_200_OK)

    @action(detail=False, methods=["put"], url_path="(?P<config_id>[0-9a-f-]{36})/update-order-status-configuration", serializer_class=OrganisationOrderConfigurationSerializer)
    def update_status_config(self, request, config_id=None, *args, **kwargs):
        configuration = get_object_or_404(OrganisationConfiguration, pk=config_id)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data['config']

        updated_config = OrganisationConfigService.update_status_config(
            config=configuration, config_data=data
        )

        return Response(
            {"config": updated_config.order_status_configuration},
            status=status.HTTP_200_OK,
        )