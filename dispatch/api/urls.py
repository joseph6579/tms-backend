from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dispatch.api.views.orders import OrderViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]