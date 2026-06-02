from django.urls import include, path

app_name = "analytics"

urlpatterns = [
    path("agent/", include("apps.analytics.urls.agent", namespace="agent")),
    path("wordlist/", include("apps.analytics.urls.wordlist", namespace="wordlist")),
    path("typification/", include("apps.analytics.urls.typification", namespace="typification")),
    path("process/", include("apps.analytics.urls.process", namespace="process")),
    path("processresult/", include("apps.analytics.urls.processresult", namespace="processresult")),
    path("audio/", include("apps.analytics.urls.audio", namespace="audio")),
    path("audioreport/", include("apps.analytics.urls.audioreport", namespace="audioreport")),
]
