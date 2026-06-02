import logging
import zipfile

from django.core.files.base import ContentFile
from django.db.models import QuerySet
from django.http import HttpResponseForbidden

from maintenance.constants import (
    API_ACTION_ADD,
    API_ACTION_EDIT,
    API_ACTION_EXPORT,
    API_ACTION_HISTORY,
    API_ACTION_HOME,
    API_ACTION_IMPORT,
    API_ACTION_LIST,
    API_ACTION_PARTIAL,
    API_ACTION_REACTIVATE,
    API_ACTION_READ,
)
from maintenance.exceptions import FormIsNotValid
from maintenance.validators import is_mp3
from maintenance.views import MaintenanceAPIView, RelatedMaintenanceAPIView
from maintenance.webevents import (
    EVENTS_FAIL_MSG,
    EVENTS_FAIL_NAME,
    EVENTS_MSG_MASC,
    EVENTS_NAME,
    EVENTS_NAME_RELATED,
    get_webevent,
)

from apps.analytics.control import Control, ControlError
from apps.analytics.forms import (
    AgentEditForm,
    AnalyticImportForm,
    AnalyticImportSearchForm,
    AudioEditForm,
    AudioReportSearchForm,
    AudioSegmentEditForm,
    PatternEditForm,
    ProcessEditForm,
    ProcessResultEditForm,
    ProcessResultSearchForm,
    ProcessSearchForm,
    TypificationEditForm,
    WordEditForm,
    WordListEditForm,
)
from apps.analytics.models import (
    Agent,
    Audio,
    AudioSegment,
    Pattern,
    Process,
    ProcessResult,
    Typification,
    Word,
    WordList,
)
from apps.analytics.utils import (
    convert_v3_to_mp3,
    convert_wav_to_mp3,
    get_duration_from_audio,
    is_v3,
    is_wav,
    process_restart_extra,
    is_zip
)
from apps.common.constants import (
    API_ACTION_CONTINUE,
    API_ACTION_EXPORT_INDIVIDUAL,
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
    MENU_PROCESS,
    MENU_RESULT,
    PROCESS_AUTO_REFRESH_SECONDS,
    PROCESS_RESULT_ERROR,
    PROCESS_RESULT_MATCH,
    PROCESS_RESULT_NO_MATCH,
    PROCESS_STATE_FINISHED,
    PROCESS_STATE_NO_AUDIOS,
    PROCESS_STATE_READY,
    PROCESS_STATE_TRANSCRIBED,
    PROJECT_NAME,
    RESTART_EXTRA_FULL,
    RESTART_EXTRA_PARTIAL,
    RESTART_EXTRA_RESET_TYPIFY,
    SEARCH_PROCESS_RESULT_MATCH,
    SEARCH_PROCESS_RESULT_NO_MATCH,
    SEARCH_PROCESS_STATE_FINISHED,
    SEARCH_PROCESS_STATE_NO_AUDIOS,
    SEARCH_PROCESS_STATE_READY,
    SEARCH_PROCESS_STATE_TRANSCRIBED,
    SLOP_MAX,
    SLOP_MIN,
)
from apps.common.views import ScopeValidationMixin

logger = logging.getLogger(__name__)


class AnalyticsMixin:
    def save_default_analytics(self, obj, save=True):
        obj.modify_user = self.user
        if obj.pk is None:
            obj.create_user = self.user
            obj.campaign = self.user.campaign
        if save:
            obj.save()

    def _export_individual(self, related_maintenance_view):
        view = related_maintenance_view()
        view.user = self.user
        view.model_name = self.model_name
        view.action = API_ACTION_EXPORT
        view.parent_model_name = self.model_name
        view.parent_object = self.object
        view.nombre_plural = self.nombre_plural.replace(" ", "_")
        return view.render_xlsx()


class AnalyticsMaintenanceAPIView(ScopeValidationMixin, AnalyticsMixin, MaintenanceAPIView):
    title = PROJECT_NAME

    def form_valid_edit(self, obj=None):
        obj = self.form.save(commit=False)
        self.save_default_analytics(obj, save=False)
        super().form_valid_edit(obj)

    def form_valid_search(self, qs: QuerySet, cleaned_data: dict) -> QuerySet:
        qs = super().form_valid_search(qs, cleaned_data)
        return self._validate_scope_before_search(qs)


class AnalyticsRelatedMaintenanceAPIView(
    ScopeValidationMixin, AnalyticsMixin, RelatedMaintenanceAPIView
):
    def form_valid_edit(self, obj=None):
        obj = self.form.save(commit=False)
        setattr(obj, self.parent_model_name, self.parent_object)
        self.save_default_analytics(obj, save=False)
        super().form_valid_edit(obj)

    def get_queryset(self):
        qs = super().get_queryset()
        return self._validate_scope_before_search(qs)


class AgentMaintenanceAPIView(AnalyticsMaintenanceAPIView):
    model = Agent
    edit_formclass = AgentEditForm
    constraints = {
        CONSTRAINT_AGENT_UNIQUE_NAME_CAMPAIGN: "Ya existe un Asesor con ese nombre en esta campaña"
    }

    def form_valid_import(self, cleaned_data: dict) -> None:
        obj = Agent(name=cleaned_data.get("name"))
        self.save_default_analytics(obj)


class WordListMaintenanceAPIView(AnalyticsMaintenanceAPIView):
    model = WordList
    edit_formclass = WordListEditForm
    import_formclass = AnalyticImportForm
    search_formclass = AnalyticImportSearchForm
    actions_get = (
        API_ACTION_HOME,
        API_ACTION_LIST,
        API_ACTION_ADD,
        API_ACTION_EDIT,
        API_ACTION_PARTIAL,
        API_ACTION_EXPORT,
        API_ACTION_IMPORT,
        API_ACTION_READ,
        API_ACTION_HISTORY,
        API_ACTION_EXPORT_INDIVIDUAL,
    )
    constraints = {
        CONSTRAINT_WORDLIST_UNIQUE_NAME_CAMPAIGN: "Ya existe una Palabra Personalizada con ese nombre en esta campaña"  # NOQA
    }

    def get(self, request, *args, **kwargs):
        if self.action == API_ACTION_EXPORT_INDIVIDUAL:
            return self._export_individual(WordRelatedMaintenanceAPIView)
        return super().get(request, *args, **kwargs)

    def import_xlsx(self):
        name = self.form.cleaned_data["name"]
        self.object = WordList(name=name)
        self.save_default_analytics(self.object)
        return super().import_xlsx()

    def form_valid_import(self, cleaned_data: dict) -> None:
        obj = Word(wordlist=self.object, word=cleaned_data.get("word"))
        self.save_default_analytics(obj)

    def render_no_html(self, success, msg):
        self.webevent = get_webevent(self.action, is_masc=False)
        return super().render_no_html(success, msg)


class WordRelatedMaintenanceAPIView(AnalyticsRelatedMaintenanceAPIView):
    model = Word
    parent_model = WordList
    order_by = ("-is_active", "pk")
    field_list = {
        API_ACTION_LIST: ["id", "word", "is_active"],
        API_ACTION_EXPORT: ["word", "is_active"],
    }
    edit_formclass = WordEditForm
    constraints = {
        CONSTRAINT_WORD_UNIQUE_WORD_WORDLIST: "Ya existe esta Palabra en esta palabra personalizada"
    }

    def render_no_html(self, success, msg):
        self.webevent = get_webevent(self.action, is_masc=False, is_related=True)
        return super().render_no_html(success, msg)


class PatternRelatedMaintenanceAPIView(AnalyticsRelatedMaintenanceAPIView):
    model = Pattern
    parent_model = Typification
    order_by = ("-is_active", "pk")
    field_list = {
        API_ACTION_LIST: ["id", "sentence", "is_active"],
        API_ACTION_EXPORT: ["sentence", "is_active"],
    }
    edit_formclass = PatternEditForm
    constraints = {
        CONSTRAINT_PATTERN_UNIQUE_SENTENCE_TYPIFICATION: "Ya existe un Patrón con esa oración en esta tipificación"  # NOQA
    }

    def update_context(self):
        update_context = super().update_context()
        update_context["slop_min"] = SLOP_MIN
        update_context["slop_max"] = SLOP_MAX
        return update_context


class TypificationMaintenanceAPIView(AnalyticsMaintenanceAPIView):
    model = Typification
    edit_formclass = TypificationEditForm
    import_formclass = AnalyticImportForm
    search_formclass = AnalyticImportSearchForm
    actions_get = (
        API_ACTION_HOME,
        API_ACTION_LIST,
        API_ACTION_ADD,
        API_ACTION_EDIT,
        API_ACTION_PARTIAL,
        API_ACTION_EXPORT,
        API_ACTION_IMPORT,
        API_ACTION_READ,
        API_ACTION_HISTORY,
        API_ACTION_EXPORT_INDIVIDUAL,
    )
    constraints = {
        CONSTRAINT_TYPIFICATION_UNIQUE_NAME_CAMPAIGN: "Ya existe una Tipificación con ese nombre en la campaña"  # NOQA
    }

    def get(self, request, *args, **kwargs):
        if self.action == API_ACTION_EXPORT_INDIVIDUAL:
            return self._export_individual(PatternRelatedMaintenanceAPIView)
        return super().get(request, *args, **kwargs)

    def import_xlsx(self):
        name = self.form.cleaned_data["name"]
        self.object = Typification(name=name)
        self.save_default_analytics(self.object)
        return super().import_xlsx()

    def form_valid_import(self, cleaned_data: dict) -> None:
        obj = Pattern(typification=self.object, sentence=cleaned_data.get("sentence"))
        self.save_default_analytics(obj)

    def render_no_html(self, success, msg):
        self.webevent = get_webevent(self.action, is_masc=False)
        return super().render_no_html(success, msg)


class ImportAudiosMixin:
    def _process_audio_files(self, files) -> list:  # NOQA
        audio_files = list()

        for file in files:
            if is_zip(file):
                with zipfile.ZipFile(file) as zip_file:
                    for file_name in zip_file.namelist():
                        audio_file_name = file_name.split("/")[-1]
                        uncompressed_file = ContentFile(
                            zip_file.read(file_name), name=audio_file_name
                        )
                        if is_mp3(uncompressed_file):
                            audio_files.append(uncompressed_file)
                        elif is_v3(uncompressed_file):
                            try:
                                mp3_content_file = convert_v3_to_mp3(uncompressed_file)
                            except Exception as e:
                                msg = f"Error al convertir el archivo {audio_file_name} a mp3"
                                logger.error(f"{msg}: {e}")
                                self.form.add_error(None, msg)
                                raise FormIsNotValid
                            else:
                                audio_files.append(mp3_content_file)
                        elif is_wav(uncompressed_file):
                            try:
                                mp3_content_file = convert_wav_to_mp3(uncompressed_file)
                            except Exception as e:
                                msg = f"Error al convertir el archivo {audio_file_name} a mp3"
                                logger.error(f"{msg}: {e}")
                                self.form.add_error(None, msg)
                                raise FormIsNotValid
                            else:
                                audio_files.append(mp3_content_file)

            elif is_mp3(file):
                audio_files.append(file)

            elif is_v3(file):
                try:
                    mp3_content_file = convert_v3_to_mp3(file)
                except Exception as e:
                    msg = "Error al convertir el archivo a mp3"
                    logger.error(f"{msg}: {e}")
                    self.form.add_error("file", msg)
                    raise FormIsNotValid
                else:
                    audio_files.append(mp3_content_file)

            elif is_wav(file):
                try:
                    mp3_content_file = convert_wav_to_mp3(file)
                except Exception as e:
                    msg = f"Error al convertir el archivo {audio_file_name} a mp3"
                    logger.error(f"{msg}: {e}")
                    self.form.add_error(None, msg)
                    raise FormIsNotValid
                else:
                    audio_files.append(mp3_content_file)

        return audio_files

    def _save_audio_files(self, audio_files: list, defaults: dict) -> None:
        audio_objs_to_create = list()
        process = defaults.get("process")

        for audio_file in audio_files:
            try:
                duration = get_duration_from_audio(audio_file)
            except Exception as e:
                logger.error(f"Error getting duration from audio {audio_file.name}: {e}")
                self.form.add_error("files", "El archivo adjunto no contiene audios válidos")
                raise FormIsNotValid
            else:
                audio_obj = Audio(file=audio_file, duration=duration, **defaults)
                self.save_default_analytics(audio_obj, save=False)
                audio_objs_to_create.append(audio_obj)

        _ = Audio.objects.bulk_create(audio_objs_to_create)

        process.update_state(self.user)  # signal is not called, so we update the process state here


class ProcessMaintenanceAPIView(ImportAudiosMixin, AnalyticsMaintenanceAPIView):
    model = Process
    edit_formclass = ProcessEditForm
    menu_active = MENU_PROCESS
    order_by = ("-is_active", "-is_running", "-create_date")
    select_related = ("wordlist",)
    field_list = {
        API_ACTION_LIST: ["id", "name", "type", "details"],
        API_ACTION_EXPORT: ["id", "name"],
    }
    subtitle = "Analytics: Procesamiento de Audios"
    upload_files = True
    button_no_text = True
    search_formclass = ProcessSearchForm
    actions_get = (
        API_ACTION_HOME,
        API_ACTION_LIST,
        API_ACTION_ADD,
        API_ACTION_EDIT,
        API_ACTION_PARTIAL,
        API_ACTION_IMPORT,
        API_ACTION_READ,
        API_ACTION_HISTORY,
        API_ACTION_MAIN,
    )
    actions_post = (
        API_ACTION_ADD,
        API_ACTION_EDIT,
        API_ACTION_REACTIVATE,
        API_ACTION_IMPORT,
        API_ACTION_START,
        API_ACTION_PAUSE,
        API_ACTION_CONTINUE,
        API_ACTION_RESTART,
    )
    constraints = {
        CONSTRAINT_PROCESS_UNIQUE_NAME_CREATE_USER: "Este usuario ya tiene un Proceso con ese nombre"  # NOQA
    }
    actions_with_no_object = (
        API_ACTION_HOME,
        API_ACTION_LIST,
        API_ACTION_ADD,
        API_ACTION_IMPORT,
        API_ACTION_MAIN,
    )

    def get(self, request, *args, **kwargs):
        if self.object and not self.object.can_execute_action(self.action):
            return HttpResponseForbidden()

        if self.action == API_ACTION_MAIN:
            if selected_process := request.GET.get("selected_process"):
                try:
                    self.object = self.model.objects.get(pk=int(selected_process))
                except (self.model.DoesNotExist, ValueError):
                    logger.warning(f"Process with id '{selected_process}' does not exist")
                else:
                    if not self.user.eval_perm(self.action, self.model_name, self.object):
                        return HttpResponseForbidden()

            return self._render_html()
        return super().get(request, *args, **kwargs)

    def _launch_analytic_task(self):
        from apps.analytics.tasks import launch_analyzer_task

        self.object.set_is_running(self.user)

        launch_analyzer_task.delay(self.object_pk, self.user.pk)

    def post(self, request, *args, **kwargs):  # NOQA
        if self.object and not self.object.can_execute_action(self.action):
            return HttpResponseForbidden()

        if self.action in (
            API_ACTION_START,
            API_ACTION_PAUSE,
            API_ACTION_CONTINUE,
            API_ACTION_RESTART,
        ):
            msg = ""
            success = True
            control = Control(self.object.pk)
            if self.action in (API_ACTION_START, API_ACTION_CONTINUE):
                try:
                    control.remove_pause_process()
                    self._launch_analytic_task()
                except Exception as e:
                    logger.error(
                        f"Error launching '{self.action}' in process {self.object_pk}: {e}"
                    )
                    success = False
            if self.action == API_ACTION_PAUSE:
                try:
                    control.set_pause_process(self.user.pk)
                except ControlError as e:
                    logger.error(f"Error pausing process {self.object_pk}: {e}")
                    success = False
            elif self.action == API_ACTION_RESTART:
                try:
                    extra_id = int(kwargs.get("extra_id"))
                    msg = process_restart_extra()[extra_id]
                except (TypeError, ValueError, KeyError):
                    logger.error("Invalid extra_id in restart action")
                    success = False
                    msg = "desconocida"
                else:
                    try:
                        if extra_id == RESTART_EXTRA_FULL:
                            self.object.set_is_ready(self.user)
                            control.remove_pause_process()
                            self._launch_analytic_task()
                        elif extra_id == RESTART_EXTRA_PARTIAL:
                            self.object.set_is_transcribed(self.user)
                            control.remove_pause_process()
                            self._launch_analytic_task()
                        elif extra_id == RESTART_EXTRA_RESET_TYPIFY:
                            self.object.set_is_transcribed(self.user)
                        else:  # RESTART_EXTRA_RESET_NEW
                            self.object.set_is_ready(self.user)
                    except Exception as e:
                        logger.error(
                            f"Error launching 'restart' in process {self.object_pk} with extra_id "
                            f"{extra_id}: {e}"
                        )
                        success = False
            return self.render_no_html(success=success, msg=msg)
        return super().post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if self.object and not self.object.can_execute_action(self.action):
            return HttpResponseForbidden()
        return super().delete(request, *args, **kwargs)

    def update_context(self):
        update_context = dict()
        if self.action == API_ACTION_LIST:
            auto_update_seconds = (
                PROCESS_AUTO_REFRESH_SECONDS if any([p.is_running for p in self.object_list]) else 0
            )
            update_context.update(
                {"auto_update_seconds": auto_update_seconds, "related_length": 12}
            )
        elif self.action in (API_ACTION_EDIT, API_ACTION_READ):
            update_context["form_accordion_enable"] = True
            update_context["form_accordion_show"] = False
        return update_context

    def form_valid_edit(self, obj=None):
        audio_files = list()

        if files := self.form.cleaned_data.get("files"):
            audio_files = self._process_audio_files(files)

            if not audio_files:
                self.form.add_error("files", "El archivo adjunto no contiene audios válidos")
                raise FormIsNotValid

        agent = self.form.cleaned_data.get("agent")
        agent_date = self.form.cleaned_data.get("agent_date")
        typifications = self.form.cleaned_data.get("typifications")
        obj = self.form.save(commit=False)
        self.save_default_analytics(obj, save=False)
        super().form_valid_edit(obj)

        obj.typifications.set(typifications)

        defaults = {"agent": agent, "agent_date": agent_date, "process": obj}
        self._save_audio_files(audio_files, defaults)
        return None

    def form_valid_search(self, qs: QuerySet, cleaned_data: dict) -> QuerySet:
        qs = super().form_valid_search(qs, cleaned_data)

        if cleaned_data["is_running"]:
            qs = qs.filter(is_running=True)

        if cleaned_data["only_active"]:
            qs = qs.filter(is_active=True)

        if created_by := cleaned_data["created_by"]:
            qs = qs.filter(create_user=created_by)

        state = cleaned_data["state"]
        if state:
            if state == SEARCH_PROCESS_STATE_NO_AUDIOS:
                qs = qs.filter(state=PROCESS_STATE_NO_AUDIOS)
            elif state == SEARCH_PROCESS_STATE_READY:
                qs = qs.filter(state=PROCESS_STATE_READY)
            elif state == SEARCH_PROCESS_STATE_FINISHED:
                qs = qs.filter(state=PROCESS_STATE_FINISHED)
            elif state == SEARCH_PROCESS_STATE_TRANSCRIBED:
                qs = qs.filter(state=PROCESS_STATE_TRANSCRIBED)
        return self._validate_scope_before_search(qs)

    def render_no_html(self, success, msg):
        events_name = EVENTS_NAME.copy()
        events_msg = EVENTS_MSG_MASC.copy()
        events_fail_name = EVENTS_FAIL_NAME.copy()
        events_fail_msg = EVENTS_FAIL_MSG.copy()

        events_name.update(
            {
                API_ACTION_START: "ProcessStarted",
                API_ACTION_PAUSE: "ProcessPaused",
                API_ACTION_CONTINUE: "ProcessContinued",
                API_ACTION_RESTART: "ProcessRestarted",
            }
        )
        events_msg.update(
            {
                API_ACTION_START: "Proceso iniciado correctamente",
                API_ACTION_PAUSE: "Proceso se detendrá en breve",
                API_ACTION_CONTINUE: "Proceso retomado correctamente",
                API_ACTION_RESTART: "Acción '{}' ejecutada correctamente",
            }
        )
        events_fail_name.update(
            {
                API_ACTION_START: "ProcessStartedFail",
                API_ACTION_PAUSE: "ProcessPausedFail",
                API_ACTION_CONTINUE: "ProcessContinuedFail",
                API_ACTION_RESTART: "ProcessRestartedFail",
            }
        )
        events_fail_msg.update(
            {
                API_ACTION_START: "Proceso NO se ha iniciado",
                API_ACTION_PAUSE: "No se pudo pausar el proceso",
                API_ACTION_CONTINUE: "Proceso NO se ha retomado",
                API_ACTION_RESTART: "Acción '{}' NO ejecutada correctamente",
            }
        )
        self.webevent = get_webevent(
            self.action,
            events_name=events_name,
            events_msg=events_msg,
            events_fail_name=events_fail_name,
            events_fail_msg=events_fail_msg,
        )
        return super().render_no_html(success, msg)


class AudioRelatedMaintenanceAPIView(ImportAudiosMixin, AnalyticsRelatedMaintenanceAPIView):
    model = Audio
    parent_model = Process
    order_by = ("-is_active", "pk")
    field_list = {API_ACTION_LIST: ["id", "original_filename", "duration", "agent", "agent_date"]}
    edit_formclass = AudioEditForm
    upload_files = True
    actions_get = (
        API_ACTION_LIST,
        API_ACTION_ADD,
        API_ACTION_EDIT,
        API_ACTION_READ,
        API_ACTION_HISTORY,
    )
    select_related = ("agent",)

    def get(self, request, *args, **kwargs):
        if not self.parent_object.can_execute_action(self.action, from_related=True):
            return HttpResponseForbidden()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.parent_object.can_execute_action(self.action, from_related=True):
            return HttpResponseForbidden()
        return super().post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if not self.parent_object.can_execute_action(self.action, from_related=True):
            return HttpResponseForbidden()
        return super().delete(request, *args, **kwargs)

    def update_context(self):
        update_context = super().update_context()
        update_context["modal_is_import"] = True
        if self.action in (API_ACTION_EDIT, API_ACTION_READ):
            update_context["form_accordion_enable"] = True
            update_context["form_accordion_show"] = False
        return update_context

    def form_valid_edit(self, obj=None):
        if self.action != API_ACTION_ADD:
            return super().form_valid_edit(obj)

        audio_files = list()
        if files := self.form.cleaned_data.get("files"):
            audio_files = self._process_audio_files(files)

            if not audio_files:
                self.form.add_error("files", "El archivo adjunto no contiene audios válidos")
                raise FormIsNotValid

        agent = self.form.cleaned_data.get("agent")
        agent_date = self.form.cleaned_data.get("agent_date")

        defaults = {"agent": agent, "agent_date": agent_date, "process": self.parent_object}
        self._save_audio_files(audio_files, defaults)
        return None


class AudioReportMaintenanceAPIView(AnalyticsMaintenanceAPIView):
    model = Audio
    model_name = "audioreport"
    menu_active = MENU_RESULT
    search_placeholder = "Buscar por nombre de proceso"
    order_by = ("-process", "-create_date")
    select_related = ("agent", "process")
    actions_get = (API_ACTION_HOME, API_ACTION_LIST, API_ACTION_READ, API_ACTION_EXPORT)
    subtitle = "Analytics: Resultados por Audio"
    actions_post = tuple()
    actions_delete = tuple()
    search_formclass = AudioReportSearchForm
    edit_formclass = AudioEditForm
    button_no_text = True
    field_list = {
        API_ACTION_LIST: ["original_filename", "agent", "agent_date", "process"],
        API_ACTION_READ: ["original_filename", "agent", "agent_date", "process"],
        API_ACTION_EXPORT: [
            "audio",
            "agent",
            "agent_date",
            "typification",
            "pattern_matched_sentence",
            "state",
            "score",
            "obs",
        ],
    }

    def update_context(self):
        update_context = dict()
        if self.action == API_ACTION_READ:
            fields_list = self.field_list[self.action]
            header_list = self.model.get_headers_list(fields_list)
            data_list = self.object.get_row_data(fields_list)["data"]
            update_context["read_data"] = zip(header_list, data_list)
            update_context["form_accordion_enable"] = True
            update_context["form_accordion_show"] = False
            update_context["form_show"] = False
        return update_context

    def form_valid_search(self, qs: QuerySet, cleaned_data: dict) -> QuerySet:
        if created_by := cleaned_data["created_by"]:
            qs = qs.filter(create_user=created_by)

        if cleaned_data["not_running"]:
            qs = qs.filter(process__is_running=False)

        if agent := cleaned_data["agent"]:
            qs = qs.filter(agent=agent)

        if param := cleaned_data["param"]:
            qs = qs.filter(process__name__icontains=param)

        qs = qs.prefetch_related("process_results")

        return self._validate_scope_before_search(qs)


class ProcessResultMaintenanceAPIView(AnalyticsMaintenanceAPIView):
    model = ProcessResult
    edit_formclass = ProcessResultEditForm
    search_formclass = ProcessResultSearchForm
    menu_active = MENU_RESULT
    search_placeholder = "Buscar por nombre de proceso"
    order_by = ("-process", "-create_date")
    select_related = ("audio", "typification", "agent", "process")
    actions_get = (
        API_ACTION_HOME,
        API_ACTION_LIST,
        API_ACTION_READ,
        API_ACTION_HISTORY,
        API_ACTION_EXPORT,
    )
    subtitle = "Analytics: Resultados individuales"
    actions_post = tuple()
    actions_delete = tuple()
    field_list = {
        API_ACTION_LIST: ["id", "audio", "process", "agent", "agent_date", "typification"],
        API_ACTION_READ: [
            "id",
            "process",
            "audio",
            "agent",
            "agent_date",
            "typification",
            "pattern_matched_sentence",
            "audio_segment_text",
            "state",
            "score",
            "obs",
        ],
        API_ACTION_EXPORT: [
            "id",
            "audio",
            "agent",
            "agent_date",
            "typification",
            "pattern_matched_sentence",
            "state",
            "score",
            "obs",
        ],
    }
    button_no_text = True
    constraints = {
        CONSTRAINT_PROCESSRESULT_UNIQUE_AUDIO_TYPIFICATION: "Ya existe una Tipificación para este Audio"  # NOQA
    }

    def update_context(self):
        update_context = dict()
        if self.action == API_ACTION_READ:
            fields_list = self.field_list[self.action]
            header_list = self.model.get_headers_list(fields_list)
            data_list = self.object.get_row_data(fields_list)["data"]
            update_context["read_data"] = zip(header_list, data_list)
            update_context["form_accordion_enable"] = True
            update_context["form_accordion_show"] = True
            update_context["form_show"] = False
        return update_context

    def form_valid_search(self, qs: QuerySet, cleaned_data: dict) -> QuerySet:
        if created_by := cleaned_data["created_by"]:
            qs = qs.filter(create_user=created_by)

        if cleaned_data["not_running"]:
            qs = qs.filter(process__is_running=False)

        if agent := cleaned_data["agent"]:
            qs = qs.filter(agent=agent)

        state = cleaned_data["state"]
        if state:
            if state == SEARCH_PROCESS_RESULT_MATCH:
                qs = qs.filter(state=PROCESS_RESULT_MATCH)
            elif state == SEARCH_PROCESS_RESULT_NO_MATCH:
                qs = qs.filter(state=PROCESS_RESULT_NO_MATCH)
            else:  # SEARCH_PROCESS_RESULT_ERROR
                qs = qs.filter(state=PROCESS_RESULT_ERROR)

        if param := cleaned_data["param"]:
            qs = qs.filter(process__name__icontains=param)

        return self._validate_scope_before_search(qs)


class AudioSegmentRelatedMaintenanceAPIView(AnalyticsRelatedMaintenanceAPIView):
    model = AudioSegment
    parent_model = Audio
    field_list = {API_ACTION_LIST: ["id", "speaker_label"]}
    edit_formclass = AudioSegmentEditForm
    actions_get = (API_ACTION_LIST, API_ACTION_EDIT, API_ACTION_READ)
    actions_post = (API_ACTION_EDIT,)
    actions_delete = tuple()
    order_by = ("order",)
    objects_per_page = 500
    button_no_text = True

    def get(self, request, *args, **kwargs):
        process = self.parent_object.process
        if not process.can_execute_action(self.action, from_related=True):
            return HttpResponseForbidden()

        self.user_can[API_ACTION_EDIT] = self.user_can[
            API_ACTION_EDIT
        ] and process.can_execute_action(API_ACTION_EDIT, from_related=True)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        process = self.parent_object.process
        if not process.can_execute_action(self.action, from_related=True):
            return HttpResponseForbidden()

        self.user_can[API_ACTION_EDIT] = self.user_can[
            API_ACTION_EDIT
        ] and process.can_execute_action(API_ACTION_EDIT, from_related=True)
        return super().post(request, *args, **kwargs)

    def update_context(self):
        update_context = super().update_context()
        if self.action == API_ACTION_LIST and self.object_list:
            audiosegments_per_minute = [list() for _ in range(self.parent_object.last_minute + 1)]
            for obj in self.object_list:
                audiosegments_per_minute[obj.minute].append(obj)
            update_context.update({"audiosegments_per_minute": audiosegments_per_minute})
        return update_context

    def render_no_html(self, success, msg):
        edit_event = "ObjectEditedRelatedIntra"
        events_name = EVENTS_NAME_RELATED.copy()
        events_name[API_ACTION_EDIT] = edit_event
        self.webevent = get_webevent(self.action, is_related=True, events_name=events_name)
        return super().render_no_html(success, msg)
