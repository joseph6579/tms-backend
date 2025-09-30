from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dispatch.api.views.orders import OrderManagementViewset

router = DefaultRouter()

router.register('orders', OrderManagementViewset, basename='order_management')

urlpatterns = [path('', include(router.urls))]
