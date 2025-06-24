from django.urls import path, include


urlpatterns = [
    path('', include('fleet.api.urls.drivers')),
    path('', include('fleet.api.urls.profiles')),
]
