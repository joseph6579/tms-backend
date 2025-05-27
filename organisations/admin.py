from django.contrib import admin

from organisations.models import Organisation, Package, OrganisationSubscription, OrganisationPreferences, DriverAppSettings

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