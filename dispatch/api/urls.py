from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dispatch.api.views.orders import OrderViewSet
from dispatch.api.views.trips import TripViewSet
from dispatch.api.views.tripstops import TripStopViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'trips', TripViewSet, basename='trip')
router.register(r'trip-stops', TripStopViewSet, basename='tripstop')

urlpatterns = [
    path('', include(router.urls)),
]