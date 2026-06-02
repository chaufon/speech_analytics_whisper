from django import forms
from django.core.exceptions import ValidationError

from maintenance.forms import MaintenanceBaseModelForm

from apps.analytics.utils import get_scopes
from apps.common.constants import ADMIN_ROLE_ID, SCOPE_CAMPAIGN, SCOPE_USER
from apps.users.models import Campaign, Role, User


class UserEditForm(MaintenanceBaseModelForm):
    template_name = "users/user/edit_form.html"
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "document_type",
            "document_number",
            "role",
            "campaign",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.user.is_superuser:
            self.fields["role"].queryset = Role.objects.exclude(pk=ADMIN_ROLE_ID)
            self.fields["campaign"].queryset = Campaign.objects.filter(pk=self.user.campaign_id)

        if self.instance.pk:
            self.fields["password"].required = False
            self.fields["username"].disabled = True

    def clean_username(self):
        username = self.cleaned_data["username"]
        if self.instance.pk is not None and self.instance.username != username:
            raise ValidationError("No se permite cambiar el Usuario")
        return username

    def clean_campaign(self):
        campaign = self.cleaned_data["campaign"]
        scope = self.user.role.get_scope("user")
        if scope in (SCOPE_USER, SCOPE_CAMPAIGN) and self.user.campaign != campaign:
            raise ValidationError("El usuario debe de pertenecer a la misma campaña")
        return campaign

    @property
    def show_password_field(self):
        return self.instance.pk is None


class RoleEditForm(MaintenanceBaseModelForm):
    template_name = "users/role/edit_form.html"

    class Meta:
        model = Role
        fields = (
            "name",
            "can_export_processresult",
            "can_history_processresult",
            "scope_processresult",
            "can_add_process",
            "can_edit_process",
            "can_delete_process",
            "can_history_process",
            "scope_process",
            "can_add_typification",
            "can_edit_typification",
            "can_delete_typification",
            "can_import_typification",
            "can_export_typification",
            "can_history_typification",
            "scope_typification",
            "can_add_wordlist",
            "can_edit_wordlist",
            "can_delete_wordlist",
            "can_import_wordlist",
            "can_export_wordlist",
            "can_history_wordlist",
            "scope_wordlist",
            "can_add_agent",
            "can_edit_agent",
            "can_delete_agent",
            "can_import_agent",
            "can_export_agent",
            "can_history_agent",
            "scope_agent",
            "can_add_campaign",
            "can_edit_campaign",
            "can_delete_campaign",
            "can_export_campaign",
            "can_history_campaign",
            "can_edit_config",
            "can_history_config",
            "can_add_user",
            "can_edit_user",
            "can_delete_user",
            "can_import_user",
            "can_export_user",
            "can_history_user",
            "can_change_user_password",
            "scope_user",
            "can_add_role",
            "can_edit_role",
            "can_delete_role",
            "can_export_role",
            "can_history_role",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["scope_processresult"].choices = get_scopes(allow_global=False)
        self.fields["scope_process"].choices = get_scopes(allow_global=False)
        self.fields["scope_typification"].choices = get_scopes(allow_user=False, allow_global=False)
        self.fields["scope_wordlist"].choices = get_scopes(allow_user=False, allow_global=False)
        self.fields["scope_agent"].choices = get_scopes(allow_user=False, allow_global=False)
        self.fields["scope_user"].choices = get_scopes(allow_user=False)


class UserPasswordResetForm(MaintenanceBaseModelForm):
    template_name = "users/user/user_reset_form.html"
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Nueva contraseña")

    class Meta:
        model = User
        fields = ("password",)


class CampaignEditForm(MaintenanceBaseModelForm):
    template_name = "users/campaign/edit_form.html"

    class Meta:
        model = Campaign
        fields = ("name", "description")
