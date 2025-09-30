from django.contrib import admin

from organisations.models import Organisation, Package, OrganisationSubscription, OrganisationConfiguration

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

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number', 'has_route_optimization']
    search_fields = ['name', 'email']


@admin.register(OrganisationConfiguration)
class OrganisationConfigurationAdmin(admin.ModelAdmin):
    list_display = ['organisation', 'max_users', 'max_drivers', 'timezone', 'default_language']
    search_fields = ['organisation__name']
