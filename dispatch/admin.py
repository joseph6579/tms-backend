from django.contrib import admin

# Register your models here.
from dispatch.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'coordinates']
