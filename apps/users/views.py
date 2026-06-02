import logging

from django.contrib.auth.hashers import make_password
from django.db.models import Q, QuerySet

from maintenance.constants import API_ACTION_EXPORT, API_ACTION_LIST
from maintenance.views import MaintenanceAPIView

from apps.common.constants import (
    CONSTRAINT_CAMPAIGN_UNIQUE_NAME,
    CONSTRAINT_ROLE_UNIQUE_NAME,
    CONSTRAINT_USER_UNIQUE_CAMPAIGN_ADMIN,
    CONSTRAINT_USER_UNIQUE_ROLE_ADMIN,
    CONSTRAINT_USER_UNIQUE_STAFF_USER,
    CONSTRAINT_USER_UNIQUE_SUPER_USER,
    CONSTRAINT_USER_UNIQUE_USERNAME,
    PROJECT_NAME,
)
from apps.common.views import ScopeValidationMixin
from apps.users.forms import CampaignEditForm, RoleEditForm, UserEditForm, UserPasswordResetForm
from apps.users.models import Campaign, Role, User

logger = logging.getLogger(__name__)


class UserAppBaseMaintenanceAPIView(ScopeValidationMixin, MaintenanceAPIView):
    title = PROJECT_NAME

    def form_valid_search(self, qs: QuerySet, cleaned_data: dict) -> QuerySet:
        qs = super().form_valid_search(qs, cleaned_data)
        return self._validate_scope_before_search(qs, allow_user=False)


class UserMaintenanceAPIView(UserAppBaseMaintenanceAPIView):
    model = User
    edit_formclass = UserEditForm
    reset_formclass = UserPasswordResetForm
    search_placeholder = "Buscar por nombres, apellidos o número de documento"
    field_list = {
        API_ACTION_EXPORT: ["id", "username", "first_name", "last_name", "role", "campaign"],
        API_ACTION_LIST: [
            "id",
            "username",
            "first_name",
            "last_name",
            "role",
            "campaign",
            "is_active",
        ],
    }
    select_related = ("role",)
    order_by = ("-is_active", "username")
    constraints = {
        CONSTRAINT_USER_UNIQUE_USERNAME: "Ya existe un Usuario con este username",
        CONSTRAINT_USER_UNIQUE_ROLE_ADMIN: "Solo se permite un único usuario con rol de "
        "administrador.",
        CONSTRAINT_USER_UNIQUE_CAMPAIGN_ADMIN: "Solo se permite un usuario asociado a "
        "la campaña de administradores",
        CONSTRAINT_USER_UNIQUE_SUPER_USER: "Solo se permite un superusuario en la plataforma",
        CONSTRAINT_USER_UNIQUE_STAFF_USER: "Solo el superusuario puede acceder al Admin",
    }

    def form_valid_search(self, qs, cleaned_data):
        if param := cleaned_data["param"]:
            qs = qs.filter(
                Q(first_name__icontains=param)
                | Q(last_name__icontains=param)
                | Q(document_number__icontains=param)
            )

        return self._validate_scope_before_search(qs, allow_user=False)

    def form_valid_edit(self, obj=None):
        user = self.form.save(commit=False)
        if password := self.form.cleaned_data.get("password"):
            user.password = make_password(password)
        super().form_valid_edit(user)

    def update_context(self):
        return {"document_type_choices": self.model.get_type_document_choices_str()}

    def form_valid_import(self, cleaned_data: dict) -> None:
        if "campaign_id" not in cleaned_data.keys():
            cleaned_data["campaign_id"] = self.user.campaign_id
        instance = self.model(**cleaned_data)
        instance.set_password(str(instance.password))
        instance.full_clean()
        instance.save()


class RoleMaintenanceAPIView(UserAppBaseMaintenanceAPIView):
    model = Role
    edit_formclass = RoleEditForm
    field_list = {
        API_ACTION_EXPORT: ["id", "name", "is_active"],
        API_ACTION_LIST: ["id", "name", "create_date", "modify_date", "is_active"],
    }
    constraints = {CONSTRAINT_ROLE_UNIQUE_NAME: "Ya existe un Rol con este nombre"}


class CampaignMaintenanceAPIView(UserAppBaseMaintenanceAPIView):
    model = Campaign
    edit_formclass = CampaignEditForm
    field_list = {
        API_ACTION_EXPORT: ["id", "name"],
        API_ACTION_LIST: ["id", "name", "description", "create_date", "modify_date", "is_active"],
    }
    constraints = {CONSTRAINT_CAMPAIGN_UNIQUE_NAME: "Ya existe una Campaña con este nombre"}
