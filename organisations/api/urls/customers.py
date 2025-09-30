from django.urls import include, path
from rest_framework.routers import DefaultRouter

from organisations.api.views.customers import CustomerManagementViewset

router = DefaultRouter()
router.register('customers', CustomerManagementViewset, basename='customer_management')

urlpatterns = [path('', include(router.urls))]
