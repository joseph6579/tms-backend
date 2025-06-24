from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch

from fleet.api.filters.vehicles import VehicleFilter
from fleet.api.serializers.vehicles import VehicleListSerializer, AssignVehicleSerializer
from fleet.models import Vehicle, DriverProfile, DriverProfileLogs


class VehicleManagementViewset(ReadOnlyModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleListSerializer
    search_fields = ['registration_number', 'driver_profile__first_name', 'driver_profile__last_name']
    ordering_fields = ['created_at']
    filterset_class = VehicleFilter

    def get_queryset(self):
        user = self.request.user
        organisation_id = getattr(user, 'organisation_id')
        is_superuser = getattr(user, 'is_superuser')
        role = getattr(user, 'role')
        user_id = getattr(user, 'id')
        # related_fields = ['driver_profile']
        fields = [
            'registration_number',
            'created_at',
            'updated_at',
            'vehicle_type',
            'source',
            'capacity',
            'organisation_id',
        ]
        driver_profiles = Prefetch(
            queryset=DriverProfile.objects.only('first_name', 'last_name', 'driver_id')
            .filter(organisation_id=organisation_id)
            .all(),
            lookup='driver_profile',
            to_attr='driver_profile_obj',
        )
        qs = Vehicle.objects.prefetch_related(driver_profiles).only(*fields)
        if is_superuser:
            return qs.all()
        elif organisation_id:
            return qs.filter(organisation_id=organisation_id)
        else:
            return qs.none()
        # TODO: Do drivers require to view/edit their vehicles?

    def update_vehicle(self, request, *args, **kwargs):
        # use VehicleUpdateSerializer
        pass

    @action(['post'], detail=True, url_path='assign', serializer_class=AssignVehicleSerializer)
    def assign(self, request, *args, **kwargs):
        vehicle = self.get_object()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        if profile := vehicle.driver_profile_obj.first():
            return Response(
                {'detail': 'vehicle is assigned, please unassign it to continue'}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            profile.vehicle = vehicle
            profile.save(updated_fields=['vehicle'])
            DriverProfileLogs.objects.create(profile=profile, user=request.user, reason=None, action='assign vehicle')
            return Response({'detail': 'vehicle assigned successfully'}, status=status.HTTP_200_OK)

    @action(['post'], detail=True, url_path='unassign')
    def unassign(self, request, *args, **kwargs):
        vehicle = self.get_object()
        if profile := vehicle.driver_profile_obj.first():
            profile.vehicle = None
            profile.save(updated_fields=['vehicle'])
            DriverProfileLogs.objects.create(profile=profile, user=request.user, reason=None, action='unassign vehicle')
            return Response({'detail': 'vehicle unassigned successfully'})
        else:
            return Response({'detail': 'vehicle is not assigned'}, status=status.HTTP_400_BAD_REQUEST)


# update, assign, unassign
