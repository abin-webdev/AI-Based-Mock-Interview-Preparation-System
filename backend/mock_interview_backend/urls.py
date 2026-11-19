from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def health_check(request):
    """
    Health check endpoint for Render / monitoring services.
    """
    return JsonResponse({
        'status': 'healthy',
        'system': 'AI-Based Mock Interview Preparation System',
        'version': '1.0.0'
    })


urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Health Check Endpoint
    path('api/health/', health_check, name='health_check'),

    # OpenAPI / Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Legacy Flutter Compatibility Layer
    path('myapp/', include('apps.compatibility.urls')),

    # RESTful API Layer (v1)
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/admin/', include('apps.accounts.admin_urls')),
    path('api/v1/companies/', include('apps.companies.urls')),
    path('api/v1/candidates/', include('apps.candidates.urls')),
    path('api/v1/vacancies/', include('apps.vacancies.urls')),
    path('api/v1/applications/', include('apps.applications.urls')),
    path('api/v1/tests/', include('apps.tests_app.urls')),
    path('api/v1/interviews/', include('apps.interviews.urls')),
    path('api/v1/ai-interviews/', include('apps.ai_interviews.urls')),
    path('api/v1/feedback/', include('apps.feedback.urls')),
    path('api/v1/complaints/', include('apps.complaints.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
