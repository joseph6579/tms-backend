from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from organisations.models import (
    Organisation, Package, OrganisationSubscription,
    OrganisationPreferences, DriverAppSettings, Store,
    StoreDriverGroup
)

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'max_users', 'max_drivers', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(OrganisationSubscription)
class OrganisationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organisation', 'package', 'start_date', 'end_date', 'is_active', 'payment_status']
    list_filter = ['is_active', 'payment_status']
    search_fields = ['organisation__name', 'package__name']

@admin.register(OrganisationPreferences)
class OrganisationPreferencesAdmin(admin.ModelAdmin):
    list_display = ['organisation', 'timezone', 'default_language']
    search_fields = ['organisation__name']

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number', 'has_route_optimization']
    search_fields = ['name', 'email']

@admin.register(DriverAppSettings)
class DriverAppSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'organisation',
        'allow_pickup_cancellation',
        'allow_dropoff_cancellation',
        'require_confirmation_code',
        'require_delivery_photo'
    ]
    list_filter = [
        'allow_pickup_cancellation',
        'allow_dropoff_cancellation',
        'require_confirmation_code',
        'require_delivery_photo',
        'enable_route_optimization'
    ]
    search_fields = ['organisation__name']
    fieldsets = (
        ('Organisation', {
            'fields': ('organisation',)
        }),
        ('Cancellation Settings', {
            'fields': ('allow_pickup_cancellation', 'allow_dropoff_cancellation')
        }),
        ('Delivery Confirmation', {
            'fields': (
                'require_confirmation_code',
                'require_recipient_name',
                'require_recipient_signature',
                'require_delivery_photo',
                'require_driver_notes'
            )
        }),
        ('Photo Settings', {
            'fields': ('photo_quality', 'max_photo_size_mb')
        }),
        ('Additional Settings', {
            'fields': (
                'enable_route_optimization',
                'offline_mode_enabled',
                'max_offline_duration_hours'
            )
        })
    )

@admin.register(Store)
class StoreAdmin(OSMGeoAdmin):
    list_display = [
        'name',
        'organisation',
        'code',
        'city',
        'is_active',
        'enable_auto_broadcast',
        'geofence_type'
    ]
    list_filter = [
        'is_active',
        'enable_auto_broadcast',
        'geofence_type',
        'city',
        'country'
    ]
    search_fields = [
        'name',
        'code',
        'address',
        'city',
        'organisation__name'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'organisation',
                'name',
                'code',
                'is_active'
            )
        }),
        ('Location', {
            'fields': (
                'coordinates',
                'address',
                'city',
                'state',
                'country',
                'postal_code'
            )
        }),
        ('Geofence Settings', {
            'fields': (
                'geofence_type',
                'geofence_radius_km',
                'geofence_polygon',
                'allow_geofence_override',
                'geofence_grace_period_minutes'
            )
        }),
        ('Contact Information', {
            'fields': (
                'contact_person',
                'contact_phone',
                'contact_email'
            )
        }),
        ('Operating Hours', {
            'fields': ('operating_hours',)
        }),
        ('Broadcast Settings', {
            'fields': (
                'enable_auto_broadcast',
                'broadcast_radius_km',
                'min_driver_rating',
                'broadcast_batch_size',
                'broadcast_interval_minutes',
                'max_broadcast_attempts'
            )
        }),
        ('Capacity Settings', {
            'fields': (
                'max_daily_orders',
                'max_concurrent_orders'
            )
        })
    )

@admin.register(StoreDriverGroup)
class StoreDriverGroupAdmin(admin.ModelAdmin):
    list_display = [
        'store',
        'driver_group',
        'priority',
        'max_delivery_distance_km',
        'max_orders_per_trip',
        'is_active'
    ]
    list_filter = [
        'is_active',
        'priority',
        'store__city'
    ]
    search_fields = [
        'store__name',
        'driver_group__name'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'store',
                'driver_group',
                'is_active'
            )
        }),
        ('Priority Settings', {
            'fields': ('priority',)
        }),
        ('Delivery Limits', {
            'fields': (
                'max_delivery_distance_km',
                'max_orders_per_trip'
            )
        }),
        ('Additional Settings', {
            'fields': ('custom_broadcast_settings',)
        })
    )
    ordering = ['store', 'priority']