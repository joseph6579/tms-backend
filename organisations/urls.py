from django.urls import include, path

urlpatterns = [
    path('', include('organisations.api.urls.organisations')),
]
