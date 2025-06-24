from django.urls import path, include
from rest_framework.routers import DefaultRouter

from fleet.api.views.drivers import DriverReadOnlyViewset

router = DefaultRouter()
router.register('drivers', DriverReadOnlyViewset)

urlpatterns = [path('', include(router.urls))]
