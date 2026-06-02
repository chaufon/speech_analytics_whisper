from django.urls import path

from maintenance.constants import (
    API_ACTION_EXPORT,
    API_ACTION_HOME,
    API_ACTION_IMPORT,
    API_ACTION_LIST,
    API_ACTION_READ,
)

from apps.analytics.views import AudioReportMaintenanceAPIView

app_name = "audioreport"

urlpatterns = [
    path("", AudioReportMaintenanceAPIView.as_view(), name=f"{API_ACTION_HOME}"),
    path(f"{API_ACTION_LIST}/", AudioReportMaintenanceAPIView.as_view(), name=f"{API_ACTION_LIST}"),
    path(
        f"{API_ACTION_IMPORT}/",
        AudioReportMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_IMPORT}",
    ),
    path(
        f"{API_ACTION_EXPORT}/",
        AudioReportMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EXPORT}",
    ),
    path(
        f"{API_ACTION_READ}/<int:object_pk>/",
        AudioReportMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_READ}",
    ),
]
