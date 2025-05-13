"""
URL configuration for BILL_EAZZ project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from django.views.generic import TemplateView

# Swagger Schema Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="User Management API",
        default_version='v1',
        description="API documentation for user login, signup, profile update, and session management.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    # Application URLs
    path('user/', include('user_profile.urls')),
    path('talent/', include('talent.urls')),
    path('company/', include('company.urls')),

    # Swagger UI and Redoc URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='swagger-json'),
    path('api-auth/', include('rest_framework.urls')),
    path('chat/', include('chat.urls')),
    path('test-chat/', TemplateView.as_view(template_name='chat/test_chat.html')),
    #path('auth/', include('social_django.urls', namespace='social')),
]