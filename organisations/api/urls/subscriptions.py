from django.urls import path, include
from rest_framework.routers import DefaultRouter
from organisations.api.views.subscriptions import SubscriptionViewSet

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]