from django.urls import path

from maintenance.constants import (
    API_ACTION_ADD,
    API_ACTION_DELETE,
    API_ACTION_EDIT,
    API_ACTION_HISTORY,
    API_ACTION_LIST,
    API_ACTION_REACTIVATE,
    API_ACTION_READ,
)

from apps.analytics.views import AudioRelatedMaintenanceAPIView

app_name = "audio"

urlpatterns = [
    path(f"{API_ACTION_ADD}/", AudioRelatedMaintenanceAPIView.as_view(), name=f"{API_ACTION_ADD}"),
    path(
        f"{API_ACTION_EDIT}/<int:object_pk>/",
        AudioRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EDIT}",
    ),
    path(
        f"{API_ACTION_DELETE}/<int:object_pk>/",
        AudioRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_DELETE}",
    ),
    path(
        f"{API_ACTION_REACTIVATE}/<int:object_pk>/",
        AudioRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_REACTIVATE}",
    ),
    path(
        f"{API_ACTION_LIST}/", AudioRelatedMaintenanceAPIView.as_view(), name=f"{API_ACTION_LIST}"
    ),
    path(
        f"{API_ACTION_READ}/<int:object_pk>/",
        AudioRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_READ}",
    ),
    path(
        f"{API_ACTION_HISTORY}/<int:object_pk>/",
        AudioRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_HISTORY}",
    ),
]
