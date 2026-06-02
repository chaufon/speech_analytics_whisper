import logging
import os
import subprocess
import tempfile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

import pghistory
from maintenance.constants import (
    API_ACTION_ADD,
    API_ACTION_DELETE,
    API_ACTION_EDIT,
    API_ACTION_HISTORY,
    API_ACTION_LIST,
    API_ACTION_PARTIAL_PLUS,
    API_ACTION_REACTIVATE,
    API_ACTION_READ,
    API_ACTION_RESET,
    EMPTY_VALUE,
)
from maintenance.models import BaseCatalogo
from maintenance.utils import format_to_str

from apps.analytics.utils import (
    get_duration_from_audio,
    get_new_name_audio_folder,
    get_process_result_states,
    get_process_states,
    get_process_types,
    process_restart_extra,
)
from apps.common.constants import (
    API_ACTION_CONTINUE,
    API_ACTION_MAIN,
    API_ACTION_PAUSE,
    API_ACTION_RESTART,
    API_ACTION_START,
    CONSTRAINT_AGENT_UNIQUE_NAME_CAMPAIGN,
    CONSTRAINT_PATTERN_UNIQUE_SENTENCE_TYPIFICATION,
    CONSTRAINT_PROCESS_UNIQUE_NAME_CREATE_USER,
    CONSTRAINT_PROCESSRESULT_UNIQUE_AUDIO_TYPIFICATION,
    CONSTRAINT_TYPIFICATION_UNIQUE_NAME_CAMPAIGN,
    CONSTRAINT_WORD_UNIQUE_WORD_WORDLIST,
    CONSTRAINT_WORDLIST_UNIQUE_NAME_CAMPAIGN,
    JOB_AWS_TRANSCRIBE_PREFIX,
    PROCESS_RESULT_ERROR,
    PROCESS_RESULT_MATCH,
    PROCESS_RESULT_NO_MATCH,
    PROCESS_STATE_FINISHED,
    PROCESS_STATE_FINISHED_PARTIAL,
    PROCESS_STATE_NO_AUDIOS,
    PROCESS_STATE_READY,
    PROCESS_STATE_TRANSCRIBED,
    PROCESS_STATE_TRANSCRIBED_PARTIAL,
    PROCESS_TYPE_AWS,
    PROCESS_TYPE_LOCAL,
    RESTART_EXTRA_FULL,
    RESTART_EXTRA_PARTIAL,
    RESTART_EXTRA_RESET_NEW,
    RESTART_EXTRA_RESET_TYPIFY,
)
from apps.users.models import Campaign, User

logger = logging.getLogger(__name__)


class AnalyticsBaseModel(BaseCatalogo):
    name = None
    create_user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Creado por", editable=False, related_name="+"
    )
    modify_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Último editor",
        editable=False,
        related_name="+",
        db_index=False,
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.PROTECT, verbose_name="Campaña", editable=False, related_name="+"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)


@pghistory.track()
class Agent(AnalyticsBaseModel):
    name = models.CharField("Nombre Completo")

    class Meta:
        verbose_name = "Asesor"
        verbose_name_plural = "Asesores"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "campaign"], name=CONSTRAINT_AGENT_UNIQUE_NAME_CAMPAIGN
            )
        ]


@pghistory.track()
class WordList(AnalyticsBaseModel):
    name = models.CharField("Nombre")

    class Meta:
        verbose_name = "Palabras Personalizadas"
        verbose_name_plural = "Palabras Personalizadas"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "campaign"], name=CONSTRAINT_WORDLIST_UNIQUE_NAME_CAMPAIGN
            )
        ]

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self.words.update(is_active=False, modify_date=timezone.now())
            self.is_active = False
            self.save(update_fields=("is_active",))

    def reactivate(self, *args, **kwargs):
        with transaction.atomic():
            self.words(manager="todos").update(is_active=True, modify_date=timezone.now())
            self.is_active = True
            self.save(update_fields=("is_active",))

    @property
    def has_related_model(self):
        return True

    @property
    def related_url(self):
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}:word:{API_ACTION_LIST}",
            args=(self.pk,),
        )

    @property
    def export_individual_url(self):
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}:export_individual", args=(self.pk,)
        )


@pghistory.track()
class Word(AnalyticsBaseModel):
    word = models.CharField("Palabra")
    wordlist = models.ForeignKey(
        WordList,
        on_delete=models.CASCADE,
        verbose_name="Palabras personalizadas",
        editable=False,
        related_name="words",
    )

    class Meta:
        verbose_name = "Palabra"
        constraints = [
            models.UniqueConstraint(
                fields=("word", "wordlist"), name=CONSTRAINT_WORD_UNIQUE_WORD_WORDLIST
            )
        ]

    @property
    def edit_url(self):
        return reverse(
            f"analytics:wordlist:word:{API_ACTION_EDIT}", args=(self.wordlist_id, self.pk)
        )

    @property
    def delete_url(self):
        return reverse(
            f"analytics:wordlist:word:{API_ACTION_DELETE}", args=(self.wordlist_id, self.pk)
        )

    @property
    def reactivate_url(self):
        return reverse(
            f"analytics:wordlist:word:{API_ACTION_REACTIVATE}", args=(self.wordlist_id, self.pk)
        )

    @property
    def read_url(self):
        return reverse(
            f"analytics:wordlist:word:{API_ACTION_READ}", args=(self.wordlist_id, self.pk)
        )

    @property
    def reset_url(self):
        return reverse(
            f"analytics:wordlist:word:{API_ACTION_RESET}", args=(self.wordlist_id, self.pk)
        )

    @property
    def history_url(self):
        return reverse(
            f"analytics:wordlist:word:{API_ACTION_HISTORY}", args=(self.wordlist_id, self.pk)
        )

    @property
    def partial_plus_url(self):
        return reverse(
            f"analytics:wordlist:word:{API_ACTION_PARTIAL_PLUS}", args=(self.wordlist_id, self.pk)
        )


@pghistory.track()
class Typification(AnalyticsBaseModel):
    name = models.CharField("Nombre")

    class Meta:
        verbose_name = "Tipificación"
        verbose_name_plural = "Tipificaciones"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "campaign"], name=CONSTRAINT_TYPIFICATION_UNIQUE_NAME_CAMPAIGN
            )
        ]

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self.patterns.update(is_active=False, modify_date=timezone.now())
            self.is_active = False
            self.save(update_fields=("is_active",))

    def reactivate(self, *args, **kwargs):
        with transaction.atomic():
            self.patterns(manager="todos").update(is_active=True, modify_date=timezone.now())
            self.is_active = True
            self.save(update_fields=("is_active",))

    @property
    def has_related_model(self):
        return True

    @property
    def related_url(self):
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}:pattern:{API_ACTION_LIST}",
            args=(self.pk,),
        )

    @property
    def export_individual_url(self):
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}:export_individual", args=(self.pk,)
        )

    def split_per_type(self) -> tuple[list, list]:
        patterns = self.patterns.all()
        patterns_fixed = [pattern for pattern in patterns if pattern.is_fixed]
        patterns_variable = [pattern for pattern in patterns if pattern.is_variable]
        return patterns_fixed, patterns_variable


@pghistory.track()
class Pattern(AnalyticsBaseModel):
    sentence = models.CharField("Oración")
    typification = models.ForeignKey(
        Typification,
        on_delete=models.CASCADE,
        verbose_name="Tipificación",
        editable=False,
        related_name="patterns",
    )

    class Meta:
        verbose_name = "Patrón"
        verbose_name_plural = "Patrones"
        constraints = [
            models.UniqueConstraint(
                fields=("sentence", "typification"),
                name=CONSTRAINT_PATTERN_UNIQUE_SENTENCE_TYPIFICATION,
            )
        ]

    @property
    def cleaned_sentence(self) -> str:
        return self.sentence.replace(f"[{self.slop}]", "") if self.is_variable else self.sentence

    @cached_property
    def slop(self):
        sentences = self.sentence.split("[")
        return int(sentences[1].split("]")[0]) if len(sentences) > 1 else 0

    @property
    def is_variable(self):
        return self.slop > 0

    @property
    def is_fixed(self):
        return self.slop == 0

    @property
    def edit_url(self):
        return reverse(
            f"analytics:typification:pattern:{API_ACTION_EDIT}",
            args=(self.typification_id, self.pk),
        )

    @property
    def delete_url(self):
        return reverse(
            f"analytics:typification:pattern:{API_ACTION_DELETE}",
            args=(self.typification_id, self.pk),
        )

    @property
    def reactivate_url(self):
        return reverse(
            f"analytics:typification:pattern:{API_ACTION_REACTIVATE}",
            args=(self.typification_id, self.pk),
        )

    @property
    def read_url(self):
        return reverse(
            f"analytics:typification:pattern:{API_ACTION_READ}",
            args=(self.typification_id, self.pk),
        )

    @property
    def reset_url(self):
        return reverse(
            f"analytics:typification:pattern:{API_ACTION_RESET}",
            args=(self.typification_id, self.pk),
        )

    @property
    def history_url(self):
        return reverse(
            f"analytics:typification:pattern:{API_ACTION_HISTORY}",
            args=(self.typification_id, self.pk),
        )

    @property
    def partial_plus_url(self):
        return reverse(
            f"analytics:typification:pattern:{API_ACTION_PARTIAL_PLUS}",
            args=(self.typification_id, self.pk),
        )


@pghistory.track()
class Process(AnalyticsBaseModel):
    name = models.CharField("Nombre")
    wordlist = models.ForeignKey(
        WordList,
        on_delete=models.PROTECT,
        verbose_name="Palabras Personalizadas",
        related_name="+",
        db_index=False,
        null=True,
    )
    typifications = models.ManyToManyField(
        Typification,
        verbose_name="Tipificaciones",
        help_text="Mantenga presionado Ctrl para seleccionar varias",
    )
    state = models.IntegerField(
        "Estado", choices=get_process_states, default=PROCESS_STATE_NO_AUDIOS, editable=False
    )
    type = models.PositiveSmallIntegerField(
        "Tipo", choices=get_process_types, default=PROCESS_TYPE_LOCAL
    )
    tries = models.PositiveSmallIntegerField("Intentos", default=0, editable=False)
    start_process = models.DateTimeField("Hora de inicio", null=True, editable=False)
    end_transcribe_upload_audios = models.DateTimeField(
        "Fin de subida de audios", null=True, editable=False
    )
    end_transcribe_create_jobs = models.DateTimeField(
        "Fin de creación de Tareas de transcripción", null=True, editable=False
    )
    end_transcribe_get_results = models.DateTimeField(
        "Fin de obtener resultados de transcripción", null=True, editable=False
    )
    end_typify_start = models.DateTimeField(
        "Fin de creación de migración a Elasticsearch", null=True, editable=False
    )
    end_typify_get_results = models.DateTimeField(
        "Fin de obtener resultados de queries", null=True, editable=False
    )
    end_process = models.DateTimeField("Hora de fin", null=True, editable=False)
    details = models.TextField("Detalles error", blank=True, editable=False)
    had_errors = models.BooleanField("Hubo errores", default=False, editable=False)
    was_stopped = models.BooleanField("Se pausó manualmente", default=False, editable=False)
    was_stopped_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Usuario que pausó",
        null=True,
        editable=False,
        related_name="+",
        db_index=False,
    )
    was_stopped_date = models.DateTimeField("Hora pausa", null=True, editable=False)
    is_running = models.BooleanField(
        "Se está procesando actualmente", default=False, editable=False
    )

    class Meta:
        verbose_name = "Procesado de Audios"
        verbose_name_plural = "Procesados de Audios"
        constraints = (
            models.UniqueConstraint(
                fields=("name", "create_user"), name=CONSTRAINT_PROCESS_UNIQUE_NAME_CREATE_USER
            ),
        )

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self.delete_from_elasticsearch()
            self.delete_process_results()
            self.delete_audio_segments()
            self.audios.update(is_active=False, modify_date=timezone.now())
            self.state = PROCESS_STATE_NO_AUDIOS
            self.is_active = False
            self.save(update_fields=("state", "is_active"))

    def reactivate(self, *args, **kwargs):
        with transaction.atomic():
            self.audios(manager="todos").update(is_active=True, modify_date=timezone.now())
            self.is_active = True
            self.state = self.calculate_state()
            self.save(update_fields=("is_active", "state"))

    def delete_from_elasticsearch(self, audios: list = None) -> None:
        from elasticsearch.exceptions import ConflictError, NotFoundError

        from apps.analytics.documents import AudioSegmentDocument

        if not audios:
            audios = self.all_audios

        try:
            _ = (
                AudioSegmentDocument.search()
                .query("terms", audio_id=[a.pk for a in audios])
                .delete()
            )
        except (NotFoundError, ConflictError):
            pass
        except Exception:
            raise

    def create_in_elasticsearch(self, audios: list = None) -> None:
        from apps.analytics.documents import AudioSegmentDocument

        if not audios:
            audios = self.all_audios

        all_segments = AudioSegment.objects.filter(audio__in=audios)

        _ = AudioSegmentDocument().update(all_segments, refresh=True)

    def delete_process_results(self, audios: list = None) -> None:
        if not audios:
            audios = self.all_audios

        _ = ProcessResult.objects.filter(audio__in=audios).delete()

    def delete_audio_segments(self, audios: list = None) -> None:
        if not audios:
            audios = self.all_audios

        _ = AudioSegment.objects.filter(audio__in=audios).delete()

    @cached_property
    def all_audios(self):
        return list(self.audios.all())

    @property
    def is_empty(self):
        return self.state == PROCESS_STATE_NO_AUDIOS

    @property
    def is_ready(self):
        return self.state == PROCESS_STATE_READY

    @property
    def is_transcribed(self):
        return self.state == PROCESS_STATE_TRANSCRIBED

    @property
    def is_partially_transcribed(self):
        return self.state == PROCESS_STATE_TRANSCRIBED_PARTIAL

    @property
    def is_finished(self):
        return self.state == PROCESS_STATE_FINISHED

    @property
    def is_partially_finished(self):
        return self.state == PROCESS_STATE_FINISHED_PARTIAL

    @property
    def is_paused(self):
        return self.was_stopped

    @property
    def is_failed(self):
        return self.had_errors

    @property
    def is_aws(self):
        return self.type == PROCESS_TYPE_AWS

    @property
    def is_local(self):
        return self.type == PROCESS_TYPE_LOCAL

    def calculate_state(self) -> int:
        if self.is_finished or self.is_partially_finished:
            return self.state

        audios_updated = self.audios.annotate(
            results_count=models.Count("process_results")
        ).all()  # intentionally reading from db

        if not audios_updated:
            return PROCESS_STATE_NO_AUDIOS

        all_audios_are_transcribed = all([a.transcription is not None for a in audios_updated])
        all_audios_are_not_transcribed = all([a.transcription is None for a in audios_updated])

        if all_audios_are_not_transcribed:
            return PROCESS_STATE_READY

        if all_audios_are_transcribed:
            all_audios_has_results = all(a.results_count > 0 for a in audios_updated)  # NOQA
            all_audios_has_no_results = all(a.results_count == 0 for a in audios_updated)  # NOQA

            if all_audios_has_no_results:
                return PROCESS_STATE_TRANSCRIBED

            if all_audios_has_results:
                return PROCESS_STATE_FINISHED

            return PROCESS_STATE_FINISHED_PARTIAL

        return PROCESS_STATE_TRANSCRIBED_PARTIAL

    def update_state(self, user) -> None:
        new_state = self.calculate_state()
        if self.state != new_state:
            self.state = new_state
            self.modify_user = user
            self.modify_date = timezone.now()
            self.save(update_fields=("state", "modify_user", "modify_date"))

    def set_is_ready(self, user):
        now = timezone.now()

        self.state = PROCESS_STATE_READY
        self.modify_user = user
        self.modify_date = now
        with transaction.atomic():
            self.save(update_fields=("state", "modify_user", "modify_date"))
            self.delete_from_elasticsearch()
            self.delete_process_results()
            self.delete_audio_segments()
            self.audios.filter(transcription__isnull=False).update(
                transcription=None, modify_user=user, modify_date=now
            )

    def set_is_transcribed(self, user):
        self.state = PROCESS_STATE_TRANSCRIBED
        self.modify_user = user
        self.modify_date = timezone.now()
        with transaction.atomic():
            self.save(update_fields=("state", "modify_user", "modify_date"))
            self.delete_from_elasticsearch()
            self.delete_process_results()

    def set_is_running(self, user) -> None:
        if not self.is_running:
            now = timezone.now()

            self.modify_user = user
            self.modify_date = now
            self.is_running = True
            self.start_process = now
            self.end_process = None
            self.tries = self.tries + 1
            self.had_errors = False
            self.was_stopped = False
            self.was_stopped_by = None
            self.was_stopped_date = None
            self.details = ""
            self.save(
                update_fields=(
                    "modify_user",
                    "modify_date",
                    "is_running",
                    "start_process",
                    "end_process",
                    "tries",
                    "had_errors",
                    "was_stopped",
                    "was_stopped_by",
                    "was_stopped_date",
                    "details",
                )
            )

    def set_is_not_running(self, user) -> None:
        now = timezone.now()

        self.is_running = False
        self.state = self.calculate_state()
        self.end_process = now
        self.modify_user = user
        self.modify_date = now
        self.save(
            update_fields=(
                "is_running",
                "state",
                "end_process",
                "modify_user",
                "modify_date",
                "had_errors",  # it might be updated in except clause
                "details",  # it might be updated in except clause
            )
        )

    def set_is_paused(self, user):
        now = timezone.now()

        self.was_stopped = True
        self.was_stopped_by = user
        self.was_stopped_date = now
        self.modify_user = user
        self.modify_date = now
        self.save(
            update_fields=(
                "was_stopped",
                "was_stopped_by",
                "was_stopped_date",
                "modify_user",
                "modify_date",
            )
        )

    def get_audios_for_transcription(self, user) -> list:  # TODO Is it stored in pghistory?
        audios = list()

        if self.is_running and not self.is_finished:
            now = timezone.now()
            audios_filtered = list(
                self.audios.filter(transcription__isnull=True)
            )  # intentionally reading from db
            if audios_filtered:
                try:
                    with transaction.atomic():
                        self.delete_from_elasticsearch(audios_filtered)
                        self.delete_process_results(audios_filtered)
                        self.delete_audio_segments(audios_filtered)

                        self.audios.filter(pk__in=[a.pk for a in audios_filtered]).update(
                            transcription_start_date=now,
                            transcription_end_date=None,
                            transcription=None,
                            typify_start_date=None,
                            typify_end_date=None,
                            process_error_details="",
                            modify_user=user,
                            modify_date=now,
                        )
                except Exception:
                    raise
                else:
                    audios = audios_filtered
        return audios

    def get_audios_to_typify(self, user) -> list:  # TODO Is it stored in pghistory?
        audios = list()

        if self.is_running and not self.is_finished:
            now = timezone.now()
            audios_filtered = list(
                self.audios.select_related("agent").filter(
                    transcription__isnull=False, typify_end_date__isnull=True
                )
            )  # intentionally reading from db
            if audios_filtered:
                try:
                    with transaction.atomic():
                        self.delete_from_elasticsearch(audios_filtered)
                        self.delete_process_results(audios_filtered)

                        self.audios.filter(pk__in=[a.pk for a in audios_filtered]).update(
                            typify_start_date=now,
                            typify_end_date=None,
                            process_error_details="",
                            modify_user=user,
                            modify_date=now,
                        )
                except Exception:
                    raise
                else:
                    audios = audios_filtered
        return audios

    # TEMPLATE & VIEWS

    @property
    def get_action(self):
        if self.is_running:
            return API_ACTION_PAUSE
        else:
            if self.is_empty:
                return API_ACTION_MAIN
            elif self.is_ready:
                return API_ACTION_START
            elif self.is_finished or self.is_partially_finished:
                return API_ACTION_RESTART
            return API_ACTION_CONTINUE

    @property
    def btn_state(self):
        states = get_process_states()
        size = 4

        if self.is_active:
            if self.is_failed:
                title = "Error general durante última ejecución"
                icon = "cloud-slash-fill"
                color = "danger"
            elif self.is_paused:
                title = "Proceso detenido manualmente"
                icon = "exclamation-triangle-fill"
                color = "warning"
            elif self.is_empty:
                title = states[PROCESS_STATE_NO_AUDIOS]
                icon = "ban"
                color = "danger"
            elif self.is_ready:
                title = "Transcribiendo..." if self.is_running else states[PROCESS_STATE_READY]
                icon = "file-earmark-text" if self.is_running else "send-check-fill"
                color = "secondary" if self.is_running else "primary"
            elif self.is_transcribed:
                title = "Tipificando..." if self.is_running else states[PROCESS_STATE_TRANSCRIBED]
                icon = "clipboard2-data" if self.is_running else "file-text-fill"
                color = "secondary" if self.is_running else "primary"
            elif self.is_partially_transcribed:
                title = (
                    "Procesando..."
                    if self.is_running
                    else states[PROCESS_STATE_TRANSCRIBED_PARTIAL]
                )
                icon = "clipboard2-data" if self.is_running else "file-text-fill"
                color = "secondary" if self.is_running else "warning"
            elif self.is_finished:
                title = states[PROCESS_STATE_FINISHED]
                icon = "clipboard2-check-fill"
                color = "success"
                size = 3
            elif self.is_partially_finished:
                title = states[PROCESS_STATE_FINISHED_PARTIAL]
                icon = "clipboard2-check-fill"
                color = "warning"
                size = 3
            else:
                title = "Error interno, reportar a Sistemas"
                icon = "exclamation-triangle-fill"
                color = "danger"
        else:
            title = "Eliminado"
            icon = "x-circle"
            color = "danger"

        return (
            f'<i class="bi bi-{icon} text-{color} fs-{size}" data-bs-toggle="tooltip"'
            f' data-bs-placement="top" title="{title}"></i>'
        )

    def can_execute_action(self, action: str, from_related=False) -> bool:
        invalid_actions = tuple()
        if self.is_paused or self.is_failed:
            invalid_actions = (API_ACTION_PAUSE, API_ACTION_RESTART)
        elif self.is_finished:
            invalid_actions = (
                API_ACTION_EDIT,
                API_ACTION_START,
                API_ACTION_PAUSE,
                API_ACTION_CONTINUE,
                API_ACTION_REACTIVATE,
                API_ACTION_DELETE,
            )
            if from_related:
                invalid_actions += (API_ACTION_ADD,)
        elif self.is_partially_finished:
            invalid_actions = (
                API_ACTION_EDIT,
                API_ACTION_START,
                API_ACTION_PAUSE,
                API_ACTION_CONTINUE,
            )
            if from_related:
                invalid_actions += (API_ACTION_ADD,)
        elif self.is_running:
            invalid_actions = (
                API_ACTION_EDIT,
                API_ACTION_DELETE,
                API_ACTION_REACTIVATE,
                API_ACTION_START,
                API_ACTION_CONTINUE,
                API_ACTION_RESTART,
            )
            if from_related:
                invalid_actions += (API_ACTION_ADD,)
        elif self.is_empty:
            invalid_actions = (
                API_ACTION_PAUSE,
                API_ACTION_CONTINUE,
                API_ACTION_RESTART,
                API_ACTION_START,
            )
        elif self.is_ready:
            invalid_actions = (API_ACTION_PAUSE, API_ACTION_CONTINUE, API_ACTION_RESTART)
        elif not self.is_active:
            invalid_actions = (
                API_ACTION_EDIT,
                API_ACTION_START,
                API_ACTION_PAUSE,
                API_ACTION_CONTINUE,
                API_ACTION_RESTART,
            )
            if from_related:
                invalid_actions += (API_ACTION_ADD, API_ACTION_REACTIVATE, API_ACTION_DELETE)
        return action not in invalid_actions if invalid_actions else True

    @property
    def can_add_new_related(self):
        return (
            self.is_active
            and not self.is_running
            and not (self.is_finished or self.is_partially_finished)
        )

    @property
    def has_related_model(self):
        return True

    @property
    def can_be_deleted(self) -> bool:
        return self.can_execute_action(API_ACTION_DELETE)

    # STR

    @property
    def type_str(self):
        return self.get_type_display()

    @property
    def state_str(self):
        return self.get_state_display()

    @property
    def wordlist_str(self):
        return self.wordlist.name if self.wordlist else EMPTY_VALUE

    @property
    def start_process_str(self):
        return format_to_str(self.start_process, omit_seconds=False)

    @property
    def end_process_str(self):
        return format_to_str(self.end_process, omit_seconds=False)

    start_process_header = "Inicio última ejecución"
    end_process_header = "Fin última ejecución"
    tries_header = "Intentos de ejecución"

    # URLs

    @property
    def related_url(self):
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}:audio:{API_ACTION_LIST}",
            args=(self.pk,),
        )

    @property
    def start_url(self):
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}:{API_ACTION_START}", args=(self.pk,)
        )

    @property
    def pause_url(self):
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}:{API_ACTION_PAUSE}", args=(self.pk,)
        )

    @property
    def continue_url(self):
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}:{API_ACTION_CONTINUE}", args=(self.pk,)
        )

    @property
    def restart_full_url(self):
        return reverse("analytics:process:restart", args=(self.pk, RESTART_EXTRA_FULL))

    @property
    def restart_partial_url(self):
        return reverse("analytics:process:restart", args=(self.pk, RESTART_EXTRA_PARTIAL))

    @property
    def restart_reset_typify_url(self):
        return reverse("analytics:process:restart", args=(self.pk, RESTART_EXTRA_RESET_TYPIFY))

    @property
    def restart_reset_new_url(self):
        return reverse("analytics:process:restart", args=(self.pk, RESTART_EXTRA_RESET_NEW))

    @property
    def restart_full_text(self):
        return process_restart_extra().get(RESTART_EXTRA_FULL, "")

    @property
    def restart_partial_text(self):
        return process_restart_extra().get(RESTART_EXTRA_PARTIAL, "")

    @property
    def restart_reset_typify_text(self):
        return process_restart_extra().get(RESTART_EXTRA_RESET_TYPIFY, "")

    @property
    def restart_reset_new_text(self):
        return process_restart_extra().get(RESTART_EXTRA_RESET_NEW, "")


@pghistory.track()
class Audio(AnalyticsBaseModel):
    file = models.FileField(upload_to=get_new_name_audio_folder, verbose_name="Archivo de audio")
    original_filename = models.CharField(
        "Nombre original del archivo", max_length=255, editable=False
    )
    duration = models.PositiveSmallIntegerField("Duración", null=False, editable=False)
    transcription = models.JSONField("Transcripción", null=True, editable=False)
    agent = models.ForeignKey(
        Agent, on_delete=models.PROTECT, verbose_name="Asesor", related_name="+", db_index=False
    )
    agent_date = models.DateField("Fecha asesor")
    process = models.ForeignKey(
        Process,
        on_delete=models.PROTECT,
        verbose_name="Último proceso",
        editable=False,
        related_name="audios",
    )
    transcription_start_date = models.DateTimeField(
        "Fecha inicio transcripción", null=True, editable=False
    )
    transcription_end_date = models.DateTimeField(
        "Fecha fin transcripción", null=True, editable=False
    )
    typify_start_date = models.DateTimeField("Fecha inicio tipificación", null=True, editable=False)
    typify_end_date = models.DateTimeField("Fecha fin tipificación", null=True, editable=False)
    process_error_details = models.TextField("Error último proceso", editable=False)

    wav_temp_path = None
    slow_temp_path = None

    def __str__(self):
        return f"{'' if self.is_active else self.DELETED_TEXT + ' - '}{self.original_filename_str}"

    class Meta:
        verbose_name = "Audio"

    def save(self, *args, **kwargs):
        if self.pk is None:
            if settings.DJANGO_MEDIA_ROOT_IS_MOUNTED and not os.path.ismount(settings.MEDIA_ROOT):
                raise ValidationError(
                    "Error con la carpeta de red, no se puede guardar el archivo."
                )
            if not self.duration:
                self.duration = get_duration_from_audio(self.file)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self.delete_from_elasticsearch()
            self.delete_process_results()
            self.delete_audio_segments()
            self.is_active = False
            self.save(update_fields=("is_active",))

    def s3_uri(self, bucket):
        return f"s3://{bucket}/{self.file_str}"

    @property
    def is_running(self):
        return self.process.is_running

    @property
    def transcribe_job_name(self):
        return f"{JOB_AWS_TRANSCRIBE_PREFIX}_{self.pk}"

    @property
    def is_transcribed(self):
        return self.transcription is not None

    @property
    def has_results(self):
        return len(self.get_results) > 0

    def delete_from_elasticsearch(self):
        from elasticsearch.exceptions import ConflictError, NotFoundError

        from apps.analytics.documents import AudioSegmentDocument

        try:
            _ = AudioSegmentDocument.search().query("match", audio_id=self.pk).delete()
        except (NotFoundError, ConflictError):
            pass
        except Exception:
            raise

    def delete_audio_segments(self):
        self.segments.all().delete()

    def delete_process_results(self):
        self.process_results.all().delete()

    def slow_down(self, factor):
        """
        Slows down the audio file using ffmpeg with 'factor' from Campaign Config
        Returns the path to the temporary file with the slowed-down audio.
        """
        if not self.slow_temp_path:
            try:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{self.extension_str}"
                )
                temp_file.close()

                cmd = [
                    "ffmpeg",
                    "-i",
                    self.file.path,
                    "-filter:a",
                    f"atempo={factor}",
                    "-y",
                    temp_file.name,
                ]

                subprocess.run(cmd, check=True, capture_output=True)
            except Exception:
                raise
            else:
                self.slow_temp_path = temp_file.name

    def clean_slow_temp_path(self):
        if self.slow_temp_path:
            try:
                os.unlink(self.slow_temp_path)
            except Exception as e:
                logger.error(f"Error cleaning wav temp path: {e}")
            finally:
                self.slow_temp_path = None

    def convert_to_wav(self) -> None:
        if not self.wav_temp_path:
            try:
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                tmp_file.close()
                cmd = [
                    "ffmpeg",
                    "-i",
                    self.file.path,
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-y",
                    tmp_file.name,
                ]
                subprocess.run(cmd, check=True, capture_output=True)
            except Exception:
                raise
            else:
                self.wav_temp_path = tmp_file.name

    def clean_wav_temp_path(self):
        if self.wav_temp_path:
            try:
                os.unlink(self.wav_temp_path)
            except Exception as e:
                logger.error(f"Error cleaning wav temp path: {e}")
            finally:
                self.wav_temp_path = None

    def create_in_elasticsearch(self):
        from apps.analytics.documents import AudioSegmentDocument

        try:
            _ = AudioSegmentDocument().update(self.segments.all(), refresh=True)
        except Exception as e:
            raise ValidationError(
                f"Error creating Elasticsearch audio documents with id "
                f"({self.pk}): {', '.join(e.messages) if hasattr(e, 'messages') else str(e)}"
            )

    def save_transcription_completed(
        self, transcription: dict | None, user: User, factor: float | None, error: str = ""
    ):
        now = timezone.now()
        _ = self.__class__.objects.filter(pk=self.pk).update(
            transcription=transcription,
            transcription_end_date=now,
            modify_user=user,
            modify_date=now,
            process_error_details=error,
        )
        if transcription:
            self.create_audio_segments(transcription, user, factor)

    def create_audio_segments(self, transcription: dict, user: User, factor: float | None):
        audio_segments = transcription["results"]["audio_segments"]
        audio_segments_por_crear = []
        for audio_segment in audio_segments:
            # Adjust timing to compensate for the slowed-down audio
            start_time = round(float(audio_segment["start_time"]), 3)
            end_time = round(float(audio_segment["end_time"]), 3)
            if factor:
                start_time = round(start_time * factor, 3)
                end_time = round(end_time * factor, 3)
                logger.info(f"initial: {audio_segment['start_time']}, after: {start_time}")
                logger.info(f"initial: {audio_segment['end_time']}, after: {end_time}")

            data = {
                "audio": self,
                "order": audio_segment["id"],
                "text": audio_segment["transcript"],
                "start_time": start_time,
                "end_time": end_time,
                "speaker_label": audio_segment["speaker_label"],
                "create_user": user,
                "modify_user": user,
                "campaign": self.campaign,
            }
            audio_segments_por_crear.append(AudioSegment(**data))

        if audio_segments_por_crear:
            _ = AudioSegment.objects.bulk_create(audio_segments_por_crear)

    @cached_property
    def get_audiosegments_ordered(self) -> list:
        return list(self.segments.order_by("start_time"))

    @property
    def last_minute(self) -> int:
        segments = self.get_audiosegments_ordered
        return segments[-1].minute if segments else 0

    @cached_property
    def get_results(self):
        return self.process_results.all()

    @property
    def get_results_for_details(self):
        return self.process_results.select_related("typification")

    # TEMPLATE & VIEWS

    @property
    def btn_state(self):
        size = 4
        if self.is_active:
            if self.is_transcribed:
                title = "Tipificando..." if self.is_running else "Audio transcrito"
                icon = "clipboard2-data" if self.is_running else "file-text-fill"
                color = "secondary" if self.is_running else "primary"
            else:  # ready
                if self.is_running:
                    title = "Transcribiendo..."
                    icon = "file-earmark-text"
                    color = "secondary"
                else:
                    title = (
                        "Listo para REPROCESAR"
                        if self.process_error_details
                        else "Listo para procesar"
                    )
                    icon = "send-check-fill"
                    color = "warning" if self.process_error_details else "primary"
        else:
            title = "Eliminado"
            icon = "x-circle"
            color = "danger"
        return (
            f'<i class="bi bi-{icon} text-{color} fs-{size}" data-bs-toggle="tooltip"'
            f' data-bs-placement="top" title="{title}"></i>'
        )

    @property
    def can_be_deleted(self) -> bool:
        return self.process.can_execute_action(API_ACTION_DELETE, from_related=True)

    @property
    def can_be_reactivated(self) -> bool:
        return self.process.can_execute_action(API_ACTION_REACTIVATE, from_related=True)

    # STR
    @property
    def agent_date_str(self):
        return format_to_str(self.agent_date)

    @property
    def duration_str(self):
        hour, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{f'{hour}:' if hour else ''}{minutes:02d}:{seconds:02d}"

    @property
    def is_running_str(self):
        return format_to_str(self.is_running)

    @property
    def original_filename_str(self):
        return self.original_filename.split("/")[-1]

    @property
    def file_str(self):
        return os.path.basename(self.file.name)

    @property
    def file_str_header(self):
        return "Nombre de archivo en disco"

    @property
    def extension_str(self):
        return self.file_str.split(".")[-1]

    @property
    def transcription_start_date_str(self):
        return format_to_str(self.transcription_start_date, omit_seconds=False)

    @property
    def transcription_end_date_str(self):
        return format_to_str(self.transcription_end_date, omit_seconds=False)

    @property
    def typify_start_date_str(self):
        return format_to_str(self.typify_start_date, omit_seconds=False)

    @property
    def typify_end_date_str(self):
        return format_to_str(self.typify_end_date, omit_seconds=False)

    transcription_start_date_header = "Inicio última transcripción"
    transcription_end_date_header = "Fin última transcripción"
    process_error_details_header = "Errores última transcripción"
    typify_start_date_header = "Inicio última tipificación"
    typify_end_date_header = "Fin última tipificación"

    # URLs

    @property
    def edit_url(self):
        return reverse(
            f"analytics:process:audio:{API_ACTION_EDIT}", args=(self.process_id, self.pk)
        )

    @property
    def delete_url(self):
        return reverse(
            f"analytics:process:audio:{API_ACTION_DELETE}", args=(self.process_id, self.pk)
        )

    @property
    def reactivate_url(self):
        return reverse(
            f"analytics:process:audio:{API_ACTION_REACTIVATE}", args=(self.process_id, self.pk)
        )

    @property
    def read_url(self):
        return reverse(
            f"analytics:process:audio:{API_ACTION_READ}", args=(self.process_id, self.pk)
        )

    @property
    def reset_url(self):
        return reverse(
            f"analytics:process:audio:{API_ACTION_RESET}", args=(self.process_id, self.pk)
        )

    @property
    def history_url(self):
        return reverse(
            f"analytics:process:audio:{API_ACTION_HISTORY}", args=(self.process_id, self.pk)
        )

    @property
    def partial_plus_url(self):
        return reverse(
            f"analytics:process:audio:{API_ACTION_PARTIAL_PLUS}", args=(self.process_id, self.pk)
        )

    @property
    def play_url(self):
        return reverse(f"analytics:audio:audiosegment:{API_ACTION_LIST}", args=(self.pk,))

    @property
    def audioreport_url(self):
        return reverse(f"analytics:audioreport:{API_ACTION_READ}", args=(self.pk,))

    def _identify_agent(self) -> str:
        sentences_first_minute = [s for s in self.get_audiosegments_ordered if s.minute == 0]
        for sentence in sentences_first_minute:
            if "de clar" in sentence.text.lower():
                return sentence.speaker_label
        return ""


class AudioSegment(AnalyticsBaseModel):
    is_active = None
    audio = models.ForeignKey(
        Audio,
        on_delete=models.PROTECT,
        verbose_name="Audio",
        related_name="segments",
        editable=False,
    )
    order = models.PositiveIntegerField("Orden en conversación")
    text = models.TextField("Texto")
    start_time = models.FloatField("Hora de inicio")
    end_time = models.FloatField("Hora de fin")
    speaker_label = models.CharField("Interlocutor")

    objects = models.Manager()

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Segmento de audio"
        verbose_name_plural = "Segmentos de audio"

    def delete(self, *args, **kwargs):
        self.__class__.objects.filter(pk=self.pk).delete()

    @property
    def minute(self) -> int:
        return int(self.start_time // 60)

    @property
    def edit_url(self):
        return reverse(
            f"analytics:audio:audiosegment:{API_ACTION_EDIT}", args=(self.audio_id, self.pk)
        )

    @property
    def read_url(self):
        return reverse(
            f"analytics:audio:audiosegment:{API_ACTION_READ}", args=(self.audio_id, self.pk)
        )


class ProcessResult(AnalyticsBaseModel):
    is_active = None
    process = models.ForeignKey(Process, on_delete=models.PROTECT, verbose_name="Proceso origen")
    audio = models.ForeignKey(
        Audio,
        on_delete=models.PROTECT,
        verbose_name="Audio",
        related_name="process_results",
        editable=False,
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        verbose_name="Asesor",
        related_name="process_results",
        editable=False,
    )
    agent_date = models.DateField("Fecha asesor")
    typification = models.ForeignKey(
        Typification, on_delete=models.PROTECT, verbose_name="Tipificación analizada"
    )
    pattern_matched = models.ForeignKey(Pattern, on_delete=models.PROTECT, null=True)
    pattern_matched_sentence = models.CharField("Oración que hizo match", blank=True)
    audio_segment = models.ForeignKey(AudioSegment, on_delete=models.PROTECT, null=True)
    audio_segment_text = models.CharField("Transcripción coincidente", blank=True)

    state = models.PositiveSmallIntegerField(
        "Estado", choices=get_process_result_states, default=PROCESS_RESULT_NO_MATCH
    )
    score = models.FloatField("Score interno", null=True)
    obs = models.TextField("Observaciones", blank=True)

    objects = models.Manager()

    class Meta:
        verbose_name = "Análisis de audios"
        verbose_name_plural = "Análisis de audios"
        constraints = (
            models.UniqueConstraint(
                fields=("audio", "typification"),
                name=CONSTRAINT_PROCESSRESULT_UNIQUE_AUDIO_TYPIFICATION,
            ),
        )

    def __str__(self):
        return f"{self.pk} - {self.state_str}"

    def delete(self, *args, **kwargs):
        self.__class__.objects.filter(pk=self.pk).delete()

    @property
    def state_str(self):
        return self.get_state_display()

    @property
    def score_str(self) -> str:
        return format_to_str(self.score)

    @property
    def agent_date_str(self):
        return format_to_str(self.agent_date)

    @property
    def has_match(self):
        return self.state == PROCESS_RESULT_MATCH

    @property
    def has_not_match(self):
        return self.state == PROCESS_RESULT_NO_MATCH

    @property
    def has_error(self):
        return self.state == PROCESS_RESULT_ERROR

    @property
    def btn_state(self):
        states = get_process_result_states()
        size = 4
        title = states[self.state]
        if self.has_match:
            icon = "clipboard2-check-fill"
            color = "success"
        elif self.has_not_match:
            icon = "clipboard2-x"
            color = "danger"
        else:  # has_error
            icon = "x-circle"
            color = "danger"
            size = 3
        return (
            f'<i class="bi bi-{icon} text-{color} fs-{size}" data-bs-toggle="tooltip"'
            f' data-bs-placement="top" title="{title}"></i>'
        )
