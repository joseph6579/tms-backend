from django.urls import path, include


urlpatterns = [
    path('', include('fleet.api.urls.drivers')),
]
