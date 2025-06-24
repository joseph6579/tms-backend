from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.api.views.drivers import DriverViewSet
from users.api.views.drivers import DriverRegistrationViewset

router = DefaultRouter()
router.register(r"drivers", DriverViewSet, basename="driver")

urlpatterns = [
    path("", include(router.urls)),
    # path('driver/registration/', DriverRegistrationViewset.as_view())
]
