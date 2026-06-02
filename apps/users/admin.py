from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.common.admin import project_admin
from apps.users.models import Role, User


class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "first_name", "last_name", "is_staff")
    filter_horizontal = ()
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "password1", "password2")}),
    )


class RoleAdmin(admin.ModelAdmin):
    list_display = ("__str__",)


project_admin.register(User, UserAdmin)
project_admin.register(Role, RoleAdmin)
