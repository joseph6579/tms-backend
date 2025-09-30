from django.urls import include, path
from rest_framework.routers import DefaultRouter

from organisations.api.views.stores import StoreManagementViewset

router = DefaultRouter()
router.register('stores', StoreManagementViewset, basename='store_management')

urlpatterns = [path('', include(router.urls))]
