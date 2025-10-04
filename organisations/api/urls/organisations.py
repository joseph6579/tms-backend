from django.urls import include, path
from rest_framework.routers import DefaultRouter

from organisations.api.views.organisations import OrganisationViewSet

router = DefaultRouter()

router.register(r'organisations', OrganisationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
