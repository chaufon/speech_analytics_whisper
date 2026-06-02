from django.urls import path

from maintenance.constants import (
    API_ACTION_ADD,
    API_ACTION_EDIT,
    API_ACTION_EXPORT,
    API_ACTION_HISTORY,
    API_ACTION_HOME,
    API_ACTION_LIST,
    API_ACTION_READ,
)

from apps.common.views import ConfigAPIView

app_name = "config"

urlpatterns = [
    path("", ConfigAPIView.as_view(), name=f"{API_ACTION_HOME}"),
    path(f"{API_ACTION_ADD}/", ConfigAPIView.as_view(), name=f"{API_ACTION_ADD}"),
    path(f"{API_ACTION_EDIT}/<int:object_pk>/", ConfigAPIView.as_view(), name=f"{API_ACTION_EDIT}"),
    path(f"{API_ACTION_LIST}/", ConfigAPIView.as_view(), name=f"{API_ACTION_LIST}"),
    path(f"{API_ACTION_EXPORT}/", ConfigAPIView.as_view(), name=f"{API_ACTION_EXPORT}"),
    path(f"{API_ACTION_READ}/<int:object_pk>/", ConfigAPIView.as_view(), name=f"{API_ACTION_READ}"),
    path(
        f"{API_ACTION_HISTORY}/<int:object_pk>/",
        ConfigAPIView.as_view(),
        name=f"{API_ACTION_HISTORY}",
    ),
]
