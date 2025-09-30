from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dispatch.api.views.trips import TripManagementViewset

router = DefaultRouter()

router.register('trips', TripManagementViewset, basename='trip-management')

urlpatterns = [path('', include(router.urls))]
