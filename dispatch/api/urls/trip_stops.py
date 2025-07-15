from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dispatch.api.views.tripstops import TripStopViewSet

router = DefaultRouter()

router.register('trip-stops', TripStopViewSet, basename='trip-stop-management')

urlpatterns = [path('', include(router.urls))]
