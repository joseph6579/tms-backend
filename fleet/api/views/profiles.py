from rest_framework.viewsets import ReadOnlyModelViewSet

from fleet.api.serializers.profiles import DriverProfileListSerializer
from fleet.models import DriverGroup, DriverProfile


class DriverManagement(ReadOnlyModelViewSet):
    serializer_class = DriverProfileListSerializer

    def get_queryset(self):
        return DriverProfile.objects.all()
