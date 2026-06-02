from django.urls import path

from maintenance.constants import API_ACTION_ADD, API_ACTION_EDIT, API_ACTION_LIST, API_ACTION_READ

from apps.analytics.views import AudioSegmentRelatedMaintenanceAPIView

app_name = "audiosegment"

urlpatterns = [
    path(
        f"{API_ACTION_EDIT}/<int:object_pk>/",
        AudioSegmentRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_EDIT}",
    ),
    path(
        f"{API_ACTION_READ}/<int:object_pk>/",
        AudioSegmentRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_READ}",
    ),
    path(
        f"{API_ACTION_LIST}/",
        AudioSegmentRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_LIST}",
    ),
    path(
        f"{API_ACTION_ADD}/",
        AudioSegmentRelatedMaintenanceAPIView.as_view(),
        name=f"{API_ACTION_ADD}",
    ),  # needed because maintenance-app
]
