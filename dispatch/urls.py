from django.urls import path, include

urlpatterns = [
    path('', include('dispatch.api.urls')),
]