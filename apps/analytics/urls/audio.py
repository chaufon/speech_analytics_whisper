from django.urls import include, path

from maintenance.constants import API_ACTION_RELATED

app_name = "audio"

urlpatterns = [
    path(
        f"{API_ACTION_RELATED}/<int:parent_pk>/",
        include("apps.analytics.urls.audio_audiosegment", namespace="audiosegment"),
    )
]
