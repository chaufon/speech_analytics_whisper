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
    API_ACTION_PARTIAL,
    API_ACTION_REACTIVATE,
    API_ACTION_READ,
    API_ACTION_RESET,
)

from apps.users.views import UserMaintenanceAPIView

app_name = "user"

urlpatterns = [
    path("", UserMaintenanceAPIView.as_view(), name=f"{API_ACTION_HOME}"),
    path(f"{API_ACTION_ADD}/", UserMaintenanceAPIView.as_view(), name=f"{API_ACTION_ADD}"),
    path(
        f"{API_ACTION_EDIT}/<int:object_pk>/",
        UserMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EDIT}",
    ),
    path(
        f"{API_ACTION_DELETE}/<int:object_pk>/",
        UserMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_DELETE}",
    ),
    path(
        f"{API_ACTION_REACTIVATE}/<int:object_pk>/",
        UserMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_REACTIVATE}",
    ),
    path(f"{API_ACTION_LIST}/", UserMaintenanceAPIView.as_view(), name=f"{API_ACTION_LIST}"),
    path(f"{API_ACTION_PARTIAL}/", UserMaintenanceAPIView.as_view(), name=f"{API_ACTION_PARTIAL}"),
    path(f"{API_ACTION_IMPORT}/", UserMaintenanceAPIView.as_view(), name=f"{API_ACTION_IMPORT}"),
    path(f"{API_ACTION_EXPORT}/", UserMaintenanceAPIView.as_view(), name=f"{API_ACTION_EXPORT}"),
    path(
        f"{API_ACTION_READ}/<int:object_pk>/",
        UserMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_READ}",
    ),
    path(
        f"{API_ACTION_RESET}/<int:object_pk>/",
        UserMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_RESET}",
    ),
    path(
        f"{API_ACTION_HISTORY}/<int:object_pk>/",
        UserMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_HISTORY}",
    ),
]
