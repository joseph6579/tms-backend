from django.contrib import admin
from django.urls import include
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls
from rest_framework_simplejwt import views
from rest_framework.schemas import get_schema_view as gsv

TITLE = 'TMS Backend API'
DESCRIPTION = 'API for TMS Backend'
VERSION = '0.0.1'

schema_view = get_schema_view(
    openapi.Info(
        title=TITLE,
        default_version='v1',
        description=DESCRIPTION,
        terms_of_service='https://chuom.app/terms/',
        contact=openapi.Contact(email='support@chuom.app'),
        license=openapi.License(name='MIT License'),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('docs/', include_docs_urls(title=TITLE, description=DESCRIPTION, public=True)),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/v1/auth/', include('djoser.urls')),
    path('api/', include('users.api.urls.users')),
]
