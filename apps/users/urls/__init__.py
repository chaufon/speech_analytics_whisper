from django.urls import include, path

app_name = "users"
urlpatterns = [
    path("user/", include("apps.users.urls.user", namespace="user")),
    path("role/", include("apps.users.urls.role", namespace="role")),
    path("campaign/", include("apps.users.urls.campaign", namespace="campaign")),
]
