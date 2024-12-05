from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.api.views.users import Users

router = DefaultRouter()

router.register(r'', Users, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]