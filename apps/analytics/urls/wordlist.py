from django.urls import include, path

from maintenance.constants import (
    API_ACTION_ADD,
    API_ACTION_DELETE,
    API_ACTION_EDIT,
    API_ACTION_EXPORT,
    API_ACTION_HISTORY,
    API_ACTION_HOME,
    API_ACTION_IMPORT,
    API_ACTION_LIST,
    API_ACTION_REACTIVATE,
    API_ACTION_READ,
    API_ACTION_RELATED,
)

from apps.analytics.views import WordListMaintenanceAPIView
from apps.common.constants import API_ACTION_EXPORT_INDIVIDUAL

app_name = "wordlist"

urlpatterns = [
    path("", WordListMaintenanceAPIView.as_view(), name=f"{API_ACTION_HOME}"),
    path(f"{API_ACTION_ADD}/", WordListMaintenanceAPIView.as_view(), name=f"{API_ACTION_ADD}"),
    path(
        f"{API_ACTION_EDIT}/<int:object_pk>/",
        WordListMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EDIT}",
    ),
    path(
        f"{API_ACTION_DELETE}/<int:object_pk>/",
        WordListMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_DELETE}",
    ),
    path(
        f"{API_ACTION_REACTIVATE}/<int:object_pk>/",
        WordListMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_REACTIVATE}",
    ),
    path(f"{API_ACTION_LIST}/", WordListMaintenanceAPIView.as_view(), name=f"{API_ACTION_LIST}"),
    path(
        f"{API_ACTION_IMPORT}/", WordListMaintenanceAPIView.as_view(), name=f"{API_ACTION_IMPORT}"
    ),
    path(
        f"{API_ACTION_EXPORT}/", WordListMaintenanceAPIView.as_view(), name=f"{API_ACTION_EXPORT}"
    ),
    path(
        f"{API_ACTION_READ}/<int:object_pk>/",
        WordListMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_READ}",
    ),
    path(
        f"{API_ACTION_HISTORY}/<int:object_pk>/",
        WordListMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_HISTORY}",
    ),
    path(
        f"{API_ACTION_RELATED}/<int:parent_pk>/",
        include("apps.analytics.urls.wordlist_word", namespace="wordlist_word"),
    ),
    path(
        f"{API_ACTION_EXPORT_INDIVIDUAL}/<int:object_pk>/",
        WordListMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EXPORT_INDIVIDUAL}",
    ),
]
