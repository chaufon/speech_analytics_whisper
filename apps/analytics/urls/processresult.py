from django.urls import path

from maintenance.constants import (
    API_ACTION_ADD,
    API_ACTION_DELETE,
    API_ACTION_EDIT,
    API_ACTION_EXPORT,
    API_ACTION_HISTORY,
    API_ACTION_HOME,
    API_ACTION_IMPORT,
    API_ACTION_LIST,
    API_ACTION_READ,
)

from apps.analytics.views import ProcessResultMaintenanceAPIView

app_name = "processresult"

urlpatterns = [
    path("", ProcessResultMaintenanceAPIView.as_view(), name=f"{API_ACTION_HOME}"),
    path(f"{API_ACTION_ADD}/", ProcessResultMaintenanceAPIView.as_view(), name=f"{API_ACTION_ADD}"),
    path(
        f"{API_ACTION_EDIT}/<int:object_pk>/",
        ProcessResultMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EDIT}",
    ),
    path(
        f"{API_ACTION_DELETE}/<int:object_pk>/",
        ProcessResultMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_DELETE}",
    ),
    path(
        f"{API_ACTION_LIST}/", ProcessResultMaintenanceAPIView.as_view(), name=f"{API_ACTION_LIST}"
    ),
    path(
        f"{API_ACTION_IMPORT}/",
        ProcessResultMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_IMPORT}",
    ),
    path(
        f"{API_ACTION_EXPORT}/",
        ProcessResultMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EXPORT}",
    ),
    path(
        f"{API_ACTION_READ}/<int:object_pk>/",
        ProcessResultMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_READ}",
    ),
    path(
        f"{API_ACTION_HISTORY}/<int:object_pk>/",
        ProcessResultMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_HISTORY}",
    ),
]
