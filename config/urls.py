from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("appointments/", include("appointments.urls")),
    path("records/", include("records.urls")),
    path("prescriptions/", include("prescriptions.urls")),
    path("telemedicine/", include("telemedicine.urls")),
    path("notifications/", include("notifications.urls")),
    path("payments/", include("payments.urls")),
    path("reports/", include("reports.urls")),
    path("api/", include("api.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
