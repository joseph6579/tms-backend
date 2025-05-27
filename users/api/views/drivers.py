from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
import random

from users.models import Driver
from users.api.serializers.users import (
    DriverSerializer, DriverLocationUpdateSerializer,
    PasswordChangeSerializer
)
from dispatch.services.location_service import LocationService

class DriverViewSet(viewsets.ModelViewSet):
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()
    location_service = LocationService()

    def get_queryset(self):
        return Driver.objects.filter(organisation=self.request.user.organisation)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a driver"""
        driver = self.get_object()
        driver.is_active = True
        driver.status = 'available'
        driver.save()
        return Response({'status': 'driver activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a driver"""
        driver = self.get_object()
        driver.is_active = False
        driver.status = 'inactive'
        driver.save()
        return Response({'status': 'driver deactivated'})

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change driver's password"""
        driver = self.get_object()
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        if not driver.check_password(old_password):
            return Response(
                {'detail': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        driver.password = make_password(new_password)
        driver.save()
        return Response({'status': 'password updated'})

    @action(detail=True, methods=['post'])
    def generate_otp(self, request, pk=None):
        """Generate OTP for driver"""
        driver = self.get_object()
        
        # Generate 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store OTP in cache with 5-minute expiry
        cache_key = f'driver_otp_{driver.id}'
        cache.set(cache_key, otp, timeout=300)  # 5 minutes
        
        # In production, send OTP via SMS
        # For now, just return it in response
        return Response({'otp': otp})

    @action(detail=True, methods=['post'])
    def verify_otp(self, request, pk=None):
        """Verify OTP for driver"""
        driver = self.get_object()
        otp = request.data.get('otp')
        
        if not otp:
            return Response(
                {'detail': 'OTP is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cache_key = f'driver_otp_{driver.id}'
        stored_otp = cache.get(cache_key)
        
        if not stored_otp or otp != stored_otp:
            return Response(
                {'detail': 'Invalid OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Clear OTP from cache
        cache.delete(cache_key)
        return Response({'status': 'OTP verified'})

    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        driver = self.get_object()
        serializer = DriverLocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']
        
        # Update location in Redis
        success = self.location_service.update_driver_location(
            str(driver.id),
            lat,
            lon
        )
        
        if not success:
            return Response(
                {'detail': 'Failed to update location'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({'status': 'location updated'})

    @action(detail=True, methods=['get'])
    def get_location(self, request, pk=None):
        driver = self.get_object()
        location = self.location_service.get_driver_location(str(driver.id))
        
        if not location:
            return Response(
                {'detail': 'Location not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(location)