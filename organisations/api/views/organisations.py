from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from organisations.api.serializers.organisations import OrganisationSerializer
from organisations.models import Organisation
from organisations.permissions import IsMasterUser, IsMasterUserorReadOnly


class OrganisationViewSet(ModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated, IsMasterUserorReadOnly]