from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.api.views.users import UsersModelViewset

router = DefaultRouter()

router.register(r'', UsersModelViewset, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]