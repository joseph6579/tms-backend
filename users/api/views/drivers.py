from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db.models import Sum, Count
from datetime import datetime, timedelta
import random

from users.models import Driver
from users.api.serializers.users import (
    DriverSerializer, DriverLocationUpdateSerializer,
    PasswordChangeSerializer, DriverEarningsSerializer,
    DeliveryHistorySerializer
)
from dispatch.services.location_service import LocationService
from fleet.models import DriverPayment
from dispatch.models import Order

class DriverViewSet(viewsets.ModelViewSet):
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()
    location_service = LocationService()

    def get_queryset(self):
        return Driver.objects.filter(organisation=self.request.user.organisation)

    @action(detail=True, methods=['get'])
    def earnings(self, request, pk=None):
        """Get driver's earnings for different time periods"""
        driver = self.get_object()
        period = request.query_params.get('period', 'week')  # week, month, year
        date = request.query_params.get('date')  # Optional specific date

        try:
            if date:
                date = datetime.strptime(date, '%Y-%m-%d').date()
            else:
                date = timezone.now().date()
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate date ranges
        if period == 'week':
            start_date = date - timedelta(days=date.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'month':
            start_date = date.replace(day=1)
            next_month = date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        elif period == 'year':
            start_date = date.replace(month=1, day=1)
            end_date = date.replace(month=12, day=31)
        else:
            return Response(
                {'detail': 'Invalid period. Use week, month, or year'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get earnings data
        earnings = DriverPayment.objects.filter(
            driver=driver,
            period_start__date__gte=start_date,
            period_end__date__lte=end_date
        ).aggregate(
            total_earnings=Sum('total_amount'),
            total_bonus=Sum('bonus_amount'),
            total_deductions=Sum('deductions'),
            payment_count=Count('id')
        )

        # Get completed deliveries count
        completed_deliveries = Order.objects.filter(
            driver=driver,
            status='completed',
            date_delivered__date__gte=start_date,
            date_delivered__date__lte=end_date
        ).count()

        response_data = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_earnings': earnings['total_earnings'] or 0,
            'total_bonus': earnings['total_bonus'] or 0,
            'total_deductions': earnings['total_deductions'] or 0,
            'payment_count': earnings['payment_count'] or 0,
            'completed_deliveries': completed_deliveries
        }

        serializer = DriverEarningsSerializer(response_data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def delivery_history(self, request, pk=None):
        """Get driver's delivery history"""
        driver = self.get_object()
        status_filter = request.query_params.get('status')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        orders = Order.objects.filter(driver=driver)

        # Apply filters
        if status_filter:
            orders = orders.filter(status=status_filter)

        try:
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                orders = orders.filter(created_at__date__gte=start_date)
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                orders = orders.filter(created_at__date__lte=end_date)
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Order by most recent first
        orders = orders.order_by('-created_at')

        # Get page number from query params
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = DeliveryHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DeliveryHistorySerializer(orders, many=True)
        return Response(serializer.data)

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