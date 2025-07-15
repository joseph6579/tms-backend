from django.urls import path, include

urlpatterns = [
    # path('api/v1/', include('dispatch.api.urls')),
    path('', include('dispatch.api.urls.orders')),
    path('', include('dispatch.api.urls.trips')),
    path('', include('dispatch.api.urls.trip_stops')),
]
