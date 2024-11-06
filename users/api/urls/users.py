from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.api.views.users import Users

router = DefaultRouter()

router.register(r'users', Users, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]