from django.urls import include, path
from rest_framework.routers import DefaultRouter

from fleet.api.views.profiles import DriverManagement

router = DefaultRouter()
router.register('profiles', DriverManagement, basename='driver_management')

urlpatterns = [path('', include(router.urls))]
