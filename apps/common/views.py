from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.urls import reverse

from maintenance.constants import (
    API_ACTION_EDIT,
    API_ACTION_EXPORT,
    API_ACTION_HISTORY,
    API_ACTION_HOME,
    API_ACTION_LIST,
    API_ACTION_READ,
)
from maintenance.views import MaintenanceAPIView

from apps.common.constants import SCOPE_CAMPAIGN, SCOPE_NONE, SCOPE_USER
from apps.common.forms import ConfigEditForm
from apps.common.models import Config


class AnalyticsLoginView(LoginView):
    template_name = "common/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        msg = user.get_login_validation_msg()
        if msg:
            form.add_error(None, msg)
            return self.form_invalid(form)
        user.clear_other_sessions()
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        if user.can_list_process:
            return reverse("analytics:process:home")
        if user.can_list_processresult:
            return reverse("analytics:processresult:home")
        else:
            return reverse("users:user:home")


class ScopeValidationMixin:
    def _validate_scope_before_search(self, qs: QuerySet, allow_user: bool = True) -> QuerySet:
        scope = self.user.role.get_scope(self.model_name)
        if scope == SCOPE_NONE:
            qs = qs.none()
        elif scope == SCOPE_USER:
            if not allow_user:
                raise ValidationError("No se permite SCOPE_USER en 'users' app")
            qs = qs.filter(create_user=self.user)
        elif scope == SCOPE_CAMPAIGN:
            qs = qs.filter(campaign_id=self.user.campaign_id)
        return qs


class ConfigAPIView(MaintenanceAPIView):
    title = "Configuración"
    model = Config
    edit_formclass = ConfigEditForm
    order_by = tuple()
    field_list = {
        API_ACTION_LIST: ["localai_mode", "localai_use_cpu", "process_list_refresh", "comment"],
        API_ACTION_EXPORT: [
            "id",
            "audios_slow_down_enable",
            "audios_slow_down_factor",
            "process_list_refresh",
            "transcribe_get_results_max_tries",
            "transcribe_get_results_seconds_between",
            "localai_mode",
            "localai_use_cpu",
        ],
    }
    actions_get = (
        API_ACTION_HOME,
        API_ACTION_LIST,
        API_ACTION_EDIT,
        API_ACTION_EXPORT,
        API_ACTION_READ,
        API_ACTION_HISTORY,
    )
    actions_post = (API_ACTION_EDIT,)
