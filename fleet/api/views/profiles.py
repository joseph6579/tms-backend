from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response

from fleet.api.serializers.profiles import DriverProfileListSerializer, ProfileActionSerializer
from fleet.models import DriverGroup, DriverProfile, DriverProfileLogs


class DriverManagement(ReadOnlyModelViewSet):
    serializer_class = DriverProfileListSerializer

    def get_queryset(self):
        user = self.request.user
        organisation_id = getattr(user, 'organisation_id')
        is_superuser = getattr(user, 'is_superuser')
        role = getattr(user, 'role')
        user_id = getattr(user, 'id')
        related_fields = ['driver', 'vehicle', 'driver_group']
        fields = [
            'id',
            'first_name',
            'last_name',
            'national_id',
            'created_at',
            'status',
            'organisation_id',
            'driver__id',
            'driver__email',
            'driver__is_active',
            'vehicle_id',
            'vehicle__registration_number',
            'driver_group_id',
            'driver_group__name',
        ]
        qs = DriverProfile.objects.select_related(*related_fields).only(*fields)
        if is_superuser:
            return qs.all()
        elif organisation_id:
            return qs.filter(organisation_id=organisation_id).all()
        elif role == 'driver':
            return qs.filter(driver_id=user_id).all()
        else:
            qs.none()

    @action(methods=['get'], detail=True, url_path='retrieve')
    def fetch_profile(self, *args, **kwargs):
        profile = self.get_object()
        data = self.get_serializer(profile).data
        return Response(data, status=status.HTTP_200_OK)

    def update_profile(self, *args, **kwargs):
        pass

    @action(methods=['post'], detail=True, url_path='activate', serializer_class=ProfileActionSerializer)
    def activate(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not profile.active:
            profile.active = True
            profile.save(update_fields=['active'])
            reason = serializer.validated_data.get('reason', None)
            DriverProfileLogs.objects.create(
                profile=profile, user=request.user, reason=reason, action='activate profile'
            )
        return Response({'detail': 'action successful'}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='deactivate', serializer_class=ProfileActionSerializer)
    def deactivate(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: Check for incomplete trips for the current organisation
        if profile.active:
            profile.active = False
            profile.save(update_fields=['active'])
            reason = serializer.validated_data.get('reason', None)
            DriverProfileLogs.objects.create(
                profile=profile, user=request.user, reason=reason, action='deactivate profile'
            )
        return Response({'detail': 'action successful'}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='switch-online', serializer_class=ProfileActionSerializer)
    def mark_as_online(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not profile.online:
            profile.online = True
            profile.save(update_fields=['online'])
            reason = serializer.validated_data.get('reason', None)
            DriverProfileLogs.objects.create(profile=profile, user=request.user, reason=reason, action='switch online')
        return Response({'detail': 'action successful'}, status=status.HTTP_200_OK)

    def mark_as_offline(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: Check for incomplete trips for the current organisation
        if profile.online:
            profile.online = False
            profile.save(update_fields=['online'])
            reason = serializer.validated_data.get('reason', None)
            DriverProfileLogs.objects.create(profile=profile, user=request.user, reason=reason, action='switch offline')
        return Response({'detail': 'action successful'}, status=status.HTTP_200_OK)
