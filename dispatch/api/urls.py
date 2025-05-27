from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dispatch.api.views.orders import OrderViewSet
from dispatch.api.views.trips import TripViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'trips', TripViewSet, basename='trip')

urlpatterns = [
    path('', include(router.urls)),
]