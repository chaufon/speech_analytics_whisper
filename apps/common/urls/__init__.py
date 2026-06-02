from django.urls import include, path

app_name = "common"

urlpatterns = [path("config/", include("apps.common.urls.config", namespace="config"))]
