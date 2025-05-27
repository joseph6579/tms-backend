from django.urls import path, include

urlpatterns = [
    path('users/', include('users.api.urls.users')),
    path('', include('users.api.urls.drivers')),
]