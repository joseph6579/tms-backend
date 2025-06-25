from django.urls import include, path
from rest_framework.routers import DefaultRouter

from fleet.api.views.vehicles import VehicleManagementViewset

router = DefaultRouter()
router.register('vehicles', VehicleManagementViewset, basename='vehicle_management')

urlpatterns = [
    path('', include(router.urls)),
]
