from django.urls import include, path

from maintenance.constants import (
    API_ACTION_ADD,
    API_ACTION_DELETE,
    API_ACTION_EDIT,
    API_ACTION_HISTORY,
    API_ACTION_HOME,
    API_ACTION_IMPORT,
    API_ACTION_LIST,
    API_ACTION_REACTIVATE,
    API_ACTION_READ,
    API_ACTION_RELATED,
)

from apps.analytics.views import ProcessMaintenanceAPIView
from apps.common.constants import (
    API_ACTION_CONTINUE,
    API_ACTION_MAIN,
    API_ACTION_PAUSE,
    API_ACTION_RESTART,
    API_ACTION_START,
)

app_name = "process"

urlpatterns = [
    path("", ProcessMaintenanceAPIView.as_view(), name=f"{API_ACTION_HOME}"),
    path(f"{API_ACTION_ADD}/", ProcessMaintenanceAPIView.as_view(), name=f"{API_ACTION_ADD}"),
    path(
        f"{API_ACTION_EDIT}/<int:object_pk>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EDIT}",
    ),
    path(
        f"{API_ACTION_DELETE}/<int:object_pk>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_DELETE}",
    ),
    path(
        f"{API_ACTION_REACTIVATE}/<int:object_pk>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_REACTIVATE}",
    ),
    path(f"{API_ACTION_LIST}/", ProcessMaintenanceAPIView.as_view(), name=f"{API_ACTION_LIST}"),
    path(f"{API_ACTION_IMPORT}/", ProcessMaintenanceAPIView.as_view(), name=f"{API_ACTION_IMPORT}"),
    path(
        f"{API_ACTION_READ}/<int:object_pk>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_READ}",
    ),
    path(
        f"{API_ACTION_HISTORY}/<int:object_pk>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_HISTORY}",
    ),
    path(
        f"{API_ACTION_RELATED}/<int:parent_pk>/",
        include("apps.analytics.urls.process_audio", namespace="audio"),
    ),
    path(f"{API_ACTION_MAIN}/", ProcessMaintenanceAPIView.as_view(), name=f"{API_ACTION_MAIN}"),
    path(
        f"{API_ACTION_START}/<int:object_pk>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_START}",
    ),
    path(
        f"{API_ACTION_PAUSE}/<int:object_pk>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_PAUSE}",
    ),
    path(
        f"{API_ACTION_CONTINUE}/<int:object_pk>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_CONTINUE}",
    ),
    path(
        f"{API_ACTION_RESTART}/<int:object_pk>/extra/<int:extra_id>/",
        ProcessMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_RESTART}",
    ),
]
