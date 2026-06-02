import logging

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

import pghistory
from maintenance.constants import (
    API_ACTION_ADD,
    API_ACTION_DELETE,
    API_ACTION_EDIT,
    API_ACTION_EXPORT,
    API_ACTION_HOME,
    API_ACTION_LIST,
    API_ACTION_PARTIAL,
    API_ACTION_PARTIAL_PLUS,
    API_ACTION_PARTIAL_SEARCH,
    API_ACTION_REACTIVATE,
    API_ACTION_READ,
    API_ACTION_RESET,
)
from maintenance.models import BaseCatalogo, MaintenanceMixin
from maintenance.validators import only_digits

from apps.analytics.utils import get_scopes
from apps.common.constants import (
    ADMIN_CAMPAIGN_ID,
    ADMIN_ROLE_ID,
    ADMIN_USER_ID,
    API_ACTION_CONTINUE,
    API_ACTION_EXPORT_INDIVIDUAL,
    API_ACTION_MAIN,
    API_ACTION_PAUSE,
    API_ACTION_RESTART,
    API_ACTION_START,
    CONSTRAINT_CAMPAIGN_UNIQUE_NAME,
    CONSTRAINT_ROLE_UNIQUE_NAME,
    CONSTRAINT_USER_UNIQUE_CAMPAIGN_ADMIN,
    CONSTRAINT_USER_UNIQUE_ROLE_ADMIN,
    CONSTRAINT_USER_UNIQUE_STAFF_USER,
    CONSTRAINT_USER_UNIQUE_SUPER_USER,
    CONSTRAINT_USER_UNIQUE_USERNAME,
    DOCUMENT_USER_CHOICES,
    SCOPE_CAMPAIGN,
    SCOPE_GLOBAL,
    SCOPE_NONE,
    SCOPE_USER,
)

logger = logging.getLogger(__name__)


class UserCustomManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


@pghistory.track()
class Campaign(BaseCatalogo):
    description = models.TextField("Descripción", blank=True)

    class Meta:
        verbose_name = "Campaña"
        constraints = (
            models.UniqueConstraint(fields=("name",), name=CONSTRAINT_CAMPAIGN_UNIQUE_NAME),
        )

    def save(self, *args, **kwargs):
        if not self._state.adding and self.pk == ADMIN_CAMPAIGN_ID:
            raise ValidationError("No se puede modificar la campaña del administrador")
        self.name = self.name.upper()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.pk == ADMIN_CAMPAIGN_ID:
            raise ValidationError("No se puede eliminar la campaña del administrador")
        super().delete(*args, **kwargs)


@pghistory.track()
class Role(BaseCatalogo):
    can_export_processresult = models.BooleanField("Puede exportar resultados", default=False)
    can_history_processresult = models.BooleanField("Puede ver histórico de cambios", default=False)
    scope_processresult = models.SmallIntegerField(
        "Alcance del permiso", choices=get_scopes, default=SCOPE_NONE
    )

    can_add_process = models.BooleanField("Puede añadir procesos", default=False)
    can_edit_process = models.BooleanField("Puede editar procesos", default=False)
    can_delete_process = models.BooleanField("Puede eliminar/reactivar procesos", default=False)
    can_history_process = models.BooleanField("Puede ver histórico de cambios", default=False)
    scope_process = models.SmallIntegerField(
        "Alcance del permiso", choices=get_scopes, default=SCOPE_NONE
    )

    can_add_typification = models.BooleanField("Puede añadir tipificaciones", default=False)
    can_edit_typification = models.BooleanField("Puede editar tipificaciones", default=False)
    can_delete_typification = models.BooleanField(
        "Puede eliminar/reactivar tipificaciones", default=False
    )
    can_import_typification = models.BooleanField("Puede importar tipificaciones", default=False)
    can_export_typification = models.BooleanField("Puede exportar tipificaciones", default=False)
    can_history_typification = models.BooleanField("Puede ver histórico de cambios", default=False)
    scope_typification = models.SmallIntegerField(
        "Alcance del permiso", choices=get_scopes, default=SCOPE_NONE
    )

    can_add_wordlist = models.BooleanField("Puede añadir palabras personalizadas", default=False)
    can_edit_wordlist = models.BooleanField("Puede editar palabras personalizadas", default=False)
    can_delete_wordlist = models.BooleanField(
        "Puede eliminar/reactivar palabras personalizadas", default=False
    )
    can_import_wordlist = models.BooleanField(
        "Puede importar palabras personalizadas", default=False
    )
    can_export_wordlist = models.BooleanField(
        "Puede exportar palabras personalizadas", default=False
    )
    can_history_wordlist = models.BooleanField("Puede ver histórico de cambios", default=False)
    scope_wordlist = models.SmallIntegerField(
        "Alcance del permiso", choices=get_scopes, default=SCOPE_NONE
    )

    can_add_agent = models.BooleanField("Puede añadir asesores", default=False)
    can_edit_agent = models.BooleanField("Puede editar asesores", default=False)
    can_delete_agent = models.BooleanField("Puede eliminar/reactivar asesores", default=False)
    can_import_agent = models.BooleanField("Puede importar asesores", default=False)
    can_export_agent = models.BooleanField("Puede exportar asesores", default=False)
    can_history_agent = models.BooleanField("Puede ver histórico de cambios", default=False)
    scope_agent = models.SmallIntegerField(
        "Alcance del permiso", choices=get_scopes, default=SCOPE_NONE
    )

    can_add_campaign = models.BooleanField("Puede añadir campañas", default=False)
    can_edit_campaign = models.BooleanField("Puede editar campañas", default=False)
    can_delete_campaign = models.BooleanField("Puede eliminar/reactivar campañas", default=False)
    can_export_campaign = models.BooleanField("Puede exportar campañas", default=False)
    can_history_campaign = models.BooleanField("Puede ver histórico de cambios", default=False)

    can_edit_config = models.BooleanField("Puede editar configuraciones", default=False)
    can_history_config = models.BooleanField("Puede ver histórico de cambios", default=False)

    can_add_user = models.BooleanField("Puede añadir usuarios", default=False)
    can_edit_user = models.BooleanField("Puede editar usuarios", default=False)
    can_delete_user = models.BooleanField("Puede eliminar/reactivar usuarios", default=False)
    can_import_user = models.BooleanField("Puede importar usuarios", default=False)
    can_export_user = models.BooleanField("Puede exportar usuarios", default=False)
    can_history_user = models.BooleanField("Puede ver histórico de cambios", default=False)
    can_change_user_password = models.BooleanField("Puede cambiar la contraseña", default=False)
    scope_user = models.SmallIntegerField(
        "Alcance del permiso", choices=get_scopes, default=SCOPE_NONE
    )

    can_add_role = models.BooleanField("Puede añadir roles", default=False)
    can_edit_role = models.BooleanField("Puede editar roles", default=False)
    can_delete_role = models.BooleanField("Puede eliminar/reactivar roles", default=False)
    can_export_role = models.BooleanField("Puede exportar roles", default=False)
    can_history_role = models.BooleanField("Puede ver histórico de cambios", default=False)

    scope_config = SCOPE_GLOBAL
    scope_campaign = SCOPE_GLOBAL

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ("name",)
        constraints = (models.UniqueConstraint(fields=("name",), name=CONSTRAINT_ROLE_UNIQUE_NAME),)

    def save(self, *args, **kwargs):
        if not self._state.adding and self.is_admin:
            raise ValidationError("No se puede modificar el rol administrador.")
        self.name = self.name.upper()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_admin:
            raise ValidationError("No se puede eliminar el rol administrador.")
        super().delete(*args, **kwargs)

    @property
    def is_admin(self):
        return self.pk == ADMIN_ROLE_ID

    @property
    def scope_role(self):
        return SCOPE_GLOBAL

    @property
    def can_add_processresult(self):
        return False

    @property
    def can_edit_processresult(self):
        return False

    @property
    def can_delete_processresult(self):
        return False

    @property
    def can_import_processresult(self):
        return False

    @property
    def can_add_config(self):
        return False

    @property
    def can_delete_config(self):
        return False

    @property
    def can_import_config(self):
        return False

    @property
    def can_export_config(self):
        return False

    @property
    def can_list_config(self):
        return self.can_edit_config or self.can_history_config

    @property
    def can_list_processresult(self):
        return self.can_export_processresult or self.can_history_processresult

    @property
    def can_list_process(self):
        return (
            self.can_add_process
            or self.can_edit_process
            or self.can_delete_process
            or self.can_history_process
        )

    @property
    def can_list_typification(self):
        return (
            self.can_add_typification
            or self.can_edit_typification
            or self.can_delete_typification
            or self.can_import_typification
            or self.can_export_typification
            or self.can_history_typification
        )

    @property
    def can_list_wordlist(self):
        return (
            self.can_add_wordlist
            or self.can_edit_wordlist
            or self.can_delete_wordlist
            or self.can_import_wordlist
            or self.can_export_wordlist
            or self.can_history_wordlist
        )

    @property
    def can_list_agent(self):
        return (
            self.can_add_agent
            or self.can_edit_agent
            or self.can_delete_agent
            or self.can_import_agent
            or self.can_export_agent
            or self.can_history_agent
        )

    @property
    def can_list_campaign(self):
        return (
            self.can_add_campaign
            or self.can_edit_campaign
            or self.can_delete_campaign
            or self.can_export_campaign
            or self.can_history_campaign
        )

    @property
    def can_list_user(self):
        return (
            self.can_add_user
            or self.can_edit_user
            or self.can_delete_user
            or self.can_import_user
            or self.can_export_user
            or self.can_history_user
            or self.can_change_user_password
        )

    @property
    def can_import_role(self):
        return False

    @property
    def can_list_role(self):
        return (
            self.can_add_role
            or self.can_edit_role
            or self.can_delete_role
            or self.can_import_role
            or self.can_export_role
            or self.can_history_role
        )

    @property
    def can_list_maintenance(self):
        return (
            self.can_list_user
            or self.can_list_role
            or self.can_list_campaign
            or self.can_list_agent
            or self.can_list_wordlist
            or self.can_list_typification
            or self.can_list_process
            or self.can_list_processresult
        )

    def has_perm(self, action: str, model_name: str) -> bool:
        if action == API_ACTION_RESET:
            return self.can_change_user_password
        elif action in (
            API_ACTION_START,  # Process model actions
            API_ACTION_PAUSE,  # Process model actions
            API_ACTION_CONTINUE,  # Process model actions
            API_ACTION_RESTART,  # Process model actions
            API_ACTION_MAIN,  # Process model actions
        ):
            action = API_ACTION_EDIT
        elif action == API_ACTION_EXPORT_INDIVIDUAL:  # Typification and Wordlist model actions
            action = API_ACTION_EXPORT
        elif action == API_ACTION_REACTIVATE:
            action = API_ACTION_DELETE
        elif action in (
            API_ACTION_HOME,
            API_ACTION_PARTIAL,
            API_ACTION_READ,
            API_ACTION_PARTIAL_PLUS,
            API_ACTION_PARTIAL_SEARCH,
        ):
            action = API_ACTION_LIST
        return getattr(self, f"can_{action}_{model_name}", False)

    def get_scope(self, model_name: str) -> int:
        if model_name in ("audio", "audiosegment", "audioreport"):
            model_name = "process"
        elif model_name == "word":
            model_name = "wordlist"
        elif model_name == "pattern":
            model_name = "typification"
        return getattr(self, f"scope_{model_name}", SCOPE_NONE)


@pghistory.track()
class User(AbstractUser, MaintenanceMixin):
    user_permissions = None
    groups = None
    username = models.CharField("Usuario", max_length=30, validators=(only_digits,))
    document_type = models.PositiveSmallIntegerField(choices=DOCUMENT_USER_CHOICES)
    document_number = models.CharField(max_length=20, validators=(only_digits,))
    role = models.ForeignKey(Role, on_delete=models.PROTECT, verbose_name="Rol")
    campaign = models.ForeignKey(Campaign, on_delete=models.PROTECT, verbose_name="Campaña")

    REQUIRED_FIELDS = ("document_type", "document_number", "role", "campaign")
    objects = UserCustomManager()
    todos = UserManager()

    def __str__(self):
        return f"{'' if self.is_active else 'USUARIO ELIMINADO - '}{self.nombre_corto}"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ("-is_active", "first_name", "last_name")
        constraints = (
            models.UniqueConstraint(fields=("username",), name=CONSTRAINT_USER_UNIQUE_USERNAME),
            models.UniqueConstraint(
                fields=("role",),
                condition=Q(role_id=ADMIN_ROLE_ID),
                name=CONSTRAINT_USER_UNIQUE_ROLE_ADMIN,
            ),
            models.UniqueConstraint(
                fields=("campaign",),
                condition=Q(campaign_id=ADMIN_CAMPAIGN_ID),
                name=CONSTRAINT_USER_UNIQUE_CAMPAIGN_ADMIN,
            ),
            models.UniqueConstraint(
                fields=("is_superuser",),
                condition=Q(is_superuser=True),
                name=CONSTRAINT_USER_UNIQUE_SUPER_USER,
            ),
            models.UniqueConstraint(
                fields=("is_staff",),
                condition=Q(is_staff=True),
                name=CONSTRAINT_USER_UNIQUE_STAFF_USER,
            ),
        )

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.upper()
        self.last_name = self.last_name.upper()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_admin:
            raise ValidationError("No se puede eliminar el usuario administrador.")
        self.clear_other_sessions()
        self.is_active = False
        return self.save(*args, **kwargs)

    def reactivate(self, *args, **kwargs):
        self.is_active = True
        return self.save(*args, **kwargs)

    def clear_other_sessions(self):
        from django.contrib.sessions.models import Session

        user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in user_sessions:
            data = session.get_decoded()
            if data.get("_auth_user_id") == str(self.pk):
                session.delete()

    def get_login_validation_msg(self) -> str:
        msg = ""
        if not self.campaign.is_active:
            msg = "Campaña no activa. Por favor, contacte a Sistemas"
        elif not self.role.is_active:
            msg = "Rol no activo. Por favor, contacte a Sistemas"
        return msg

    def eval_perm_related(
        self, action: str, parent_model_name: str, parent_object, object_to_edit
    ) -> bool:
        if parent_model_name == "audio":  # AudiosegmentMaintenanceView sends it
            parent_model_name = "process"
        scope = self.role.get_scope(parent_model_name)
        if scope == SCOPE_NONE:
            return False

        has_perm = self.role.has_perm(action, parent_model_name)
        object_to_eval = object_to_edit
        if (
            action in (API_ACTION_ADD, API_ACTION_LIST, API_ACTION_HOME, API_ACTION_EXPORT)
            or not object_to_edit
        ):
            object_to_eval = parent_object

        if scope == SCOPE_USER:
            create_user = getattr(object_to_eval, "create_user", None)
            if not create_user:
                raise ValidationError(
                    "Se requiere 'create_user' en object_to_edit or parent_object para SCOPE_USER"
                )
            return create_user == self and has_perm
        elif scope == SCOPE_CAMPAIGN:
            return object_to_eval.campaign_id == self.campaign_id and has_perm
        else:  # scope == GLOBAL
            return has_perm

    def eval_perm(self, action: str, model_name: str, object_to_edit) -> bool:
        if (
            object_to_edit
            and isinstance(object_to_edit, User)
            and object_to_edit == self
            and action == API_ACTION_RESET
        ):
            return True  # reset own password always allowed

        if model_name == "audioreport":  # audioreport
            model_name = "process"

        scope = self.role.get_scope(model_name)
        if scope == SCOPE_NONE:
            return False

        has_perm = self.role.has_perm(action, model_name)
        if (
            action in (API_ACTION_ADD, API_ACTION_LIST, API_ACTION_HOME, API_ACTION_EXPORT)
            or not object_to_edit
        ):
            return has_perm

        if scope == SCOPE_USER:
            create_user = getattr(object_to_edit, "create_user", None)
            if not create_user:
                raise ValidationError("Se requiere 'create_user' en object_to_edit para SCOPE_USER")
            return create_user == self and has_perm
        elif scope == SCOPE_CAMPAIGN:
            return object_to_edit.campaign_id == self.campaign_id and has_perm
        else:  # scope == GLOBAL
            return has_perm

    @property
    def is_admin(self):
        return self.pk == ADMIN_USER_ID

    @classmethod
    def get_type_document_choices_str(cls):
        field = cls._meta.get_field("document_type")
        return ", ".join([f"colocar {c[0]} si {c[1]}" for c in field.choices])

    @property
    def documento_identidad(self):
        return f"{self.get_document_type_display()}: {self.document_number}"

    @property
    def nombre_corto(self):
        return f"{self.first_name.split(' ')[0]} {self.last_name.split(' ')[0]}"

    @property
    def can_add_process(self):
        return self.role.can_add_process

    @property
    def can_list_config(self):
        return self.role.can_list_config

    @property
    def can_list_campaign(self):
        return self.role.can_list_campaign

    @property
    def can_list_agent(self):
        return self.role.can_list_agent

    @property
    def can_list_processresult(self):
        return self.role.can_list_processresult

    @property
    def can_list_process(self):
        return self.role.can_list_process

    @property
    def can_list_typification(self):
        return self.role.can_list_typification

    @property
    def can_list_wordlist(self):
        return self.role.can_list_wordlist

    @property
    def can_list_maintenance(self):
        return self.role.can_list_maintenance

    @property
    def can_list_user(self):
        return self.role.can_list_user

    @property
    def can_list_role(self):
        return self.role.can_list_role

    @staticmethod
    def get_analytics_url(model: str) -> str:
        return reverse(f"analytics:{model}:home")

    @property
    def get_audio_url(self):
        return self.get_analytics_url("audio")

    @property
    def get_process_url(self):
        return self.get_analytics_url("process")

    @property
    def get_processresult_url(self):
        return self.get_analytics_url("processresult")

    @property
    def get_audioreport_url(self):
        return self.get_analytics_url("audioreport")

    @property
    def get_wordlist_url(self):
        return self.get_analytics_url("wordlist")

    @property
    def get_typification_url(self):
        return self.get_analytics_url("typification")

    @property
    def get_agent_url(self):
        return self.get_analytics_url("agent")

    @property
    def role_str(self):
        return self.role.name

    @property
    def campaign_str(self):
        return self.campaign.name
