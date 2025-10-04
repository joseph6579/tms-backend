from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dispatch.api.views.trips import TripManagementViewset
from dispatch.api.views.driver_trips import DriverTripViewSet

router = DefaultRouter()

router.register('trips', TripManagementViewset, basename='trip-management')
router.register('driver-trips', DriverTripViewSet, basename='driver-trip')

urlpatterns = [path('', include(router.urls))]
