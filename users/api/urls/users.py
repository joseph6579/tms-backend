from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.api.views.users import UsersModelViewset, GoogleLoginView, Google

router = DefaultRouter()

router.register(r'', UsersModelViewset, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('google/', Google.as_view(), name='google'),
]