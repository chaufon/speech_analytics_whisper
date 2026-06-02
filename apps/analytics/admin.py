from django.contrib import admin

from django_celery_results.models import GroupResult, TaskResult

from apps.analytics.models import Audio, Process
from apps.common.admin import project_admin


class AudioAdmin(admin.StackedInline):
    model = Audio
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class ProcessAdmin(admin.ModelAdmin):
    inlines = (AudioAdmin,)
    list_display = ("name", "id", "state", "tries", "details")
    readonly_fields = (
        "state",
        "campaign",
        "tries",
        "start_process",
        "end_transcribe_upload_audios",
        "end_transcribe_create_jobs",
        "end_transcribe_get_results",
        "end_typify_start",
        "end_typify_get_results",
        "end_process",
        "details",
        "had_errors",
        "was_stopped",
        "is_running",
    )

    def has_add_permission(self, request):
        return False


project_admin.register(Process, ProcessAdmin)
project_admin.register(TaskResult)
project_admin.register(GroupResult)
