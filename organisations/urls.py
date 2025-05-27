from django.urls import include, path

urlpatterns = [
    path('', include('organisations.api.urls.organisations')),
    path('', include('organisations.api.urls.subscriptions')),
]