from django import forms

from maintenance.constants import TODOS, TODOS_STR
from maintenance.forms import ImportForm, MaintenanceBaseModelForm
from maintenance.utils import complete_todos_choices
from maintenance.validators import is_mp3

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
    get_search_process_result_state_choices,
    get_search_process_state_choices,
    is_v3,
    is_wav,
    is_zip,
)
from apps.common.constants import SCOPE_CAMPAIGN, SLOP_MAX, SLOP_MIN
from apps.common.forms import BaseSearchForm
from apps.users.models import User


class AgentEditForm(MaintenanceBaseModelForm):
    template_name = "analytics/agent/edit_form.html"

    class Meta:
        model = Agent
        fields = ("name",)


class WordListEditForm(MaintenanceBaseModelForm):
    template_name = "analytics/wordlist/edit_form.html"

    class Meta:
        model = WordList
        fields = ("name",)


class WordEditForm(MaintenanceBaseModelForm):
    template_name = "analytics/wordlist/word/edit_form.html"

    class Meta:
        model = Word
        fields = ("word",)


class TypificationEditForm(MaintenanceBaseModelForm):
    template_name = "analytics/typification/edit_form.html"

    class Meta:
        model = Typification
        fields = ("name",)


class PatternEditForm(MaintenanceBaseModelForm):
    template_name = "analytics/typification/pattern/edit_form.html"

    class Meta:
        model = Pattern
        fields = ("sentence",)

    def clean_sentence(self):
        sentence = self.cleaned_data["sentence"]
        if len(sentence.split("[")) > 2:
            self.add_error("sentence", "Solo se permite un '[X]' o ninguno por oración")
        elif len(sentence.split("]")) > 2:
            self.add_error("sentence", "Solo se permite un '[X]' o ninguno por oración")
        else:
            if len(sentence.split("[")) == 2:
                try:
                    slop = int(sentence.split("[")[1].split("]")[0])
                except ValueError:
                    self.add_error(
                        "sentence", f"Solo se permite números enteros entre {SLOP_MIN} y {SLOP_MAX}"
                    )
                else:
                    if not (SLOP_MIN <= slop <= SLOP_MAX):
                        self.add_error(
                            "sentence",
                            f"Solo se permite números enteros entre {SLOP_MIN} y {SLOP_MAX}",
                        )
        return sentence


class AudioImportForm(MaintenanceBaseModelForm):
    files = forms.FileField(
        required=False,
        label="Archivo",
        help_text="Audio en mp3 o V3. O comprimido en 'zip' con todos los audios",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["files"].widget.attrs.update(
            {"multiple": True, "accept": "*.zip *.mp3 *.v3 *.zip *.wav"}
        )

    def clean_files(self):
        files = self.files.getlist("files")
        for file in files:
            if not (is_zip(file) or is_mp3(file) or is_v3(file) or is_wav(file)):
                raise forms.ValidationError("El archivo debe ser mp3 o V3 o wav o zip")
        return files


class ProcessEditForm(AudioImportForm):
    template_name = "analytics/process/edit_form.html"

    agent = forms.ModelChoiceField(required=False, queryset=Agent.objects.none(), label="Asesor")
    agent_date = forms.DateField(required=False, label="Fecha")

    class Meta:
        model = Process
        fields = ("name", "typifications")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agent"].queryset = Agent.objects.filter(campaign=self.user.campaign)
        self.fields["typifications"].widget.attrs["style"] = "height:150px"
        self.fields["typifications"].queryset = Typification.objects.filter(
            campaign=self.user.campaign
        )

    @property
    def has_import_errors(self):
        """Check if there are any errors in the import-related fields."""
        if not self.errors:
            return False
        return self.has_error("files") or self.has_error("agent") or self.has_error("agent_date")

    @property
    def show_import_fields(self):
        return self.instance.pk is None

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("files"):
            if not cleaned_data.get("agent"):
                self.add_error("agent", "Para importar audios, debe seleccionar un asesor")
            if not cleaned_data.get("agent_date"):
                self.add_error("agent_date", "Para importar audios, debe seleccionar una fecha")
        return cleaned_data


class ProcessResultEditForm(MaintenanceBaseModelForm):
    template_name = "analytics/processresult/edit_form.html"

    class Meta:
        model = ProcessResult
        fields = ("process", "pattern_matched_sentence", "score", "typification")


class AudioEditForm(AudioImportForm):
    template_name = "analytics/process/audio/edit_form.html"

    class Meta:
        model = Audio
        fields = ("agent", "agent_date")

    @property
    def show_import_field(self):
        return self.instance.pk is None


class AudioSegmentEditForm(MaintenanceBaseModelForm):
    template_name = "analytics/audio/audiosegment/edit_form.html"

    class Meta:
        model = AudioSegment
        fields = ("text",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text"].widget.attrs["cols"] = "58"
        self.fields["text"].widget.attrs["class"] += " h-50"


class ProcessSearchForm(BaseSearchForm):
    template_name = "analytics/process/search_form.html"

    state = forms.ChoiceField(
        required=False,
        label="Estado",
        choices=complete_todos_choices(get_search_process_state_choices()),
        initial=TODOS,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    created_by = forms.ModelChoiceField(
        required=False,
        label="Creado por",
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label=TODOS_STR,
    )
    is_running = forms.BooleanField(
        required=False,
        label="Solo Procesos en curso",
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    only_active = forms.BooleanField(
        required=False,
        label="Excluir eliminados",
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hx_trigger = self.fields["param"].widget.attrs["hx-trigger"] + (
            ", ProcessStarted from:body, ProcessPaused from:body, "
            "ProcessContinued from:body, ProcessRestarted from:body"
        )
        self.fields["param"].widget.attrs["hx-trigger"] = hx_trigger
        self.fields["is_running"].widget.attrs["hx-trigger"] = "click"
        self.fields["only_active"].widget.attrs["hx-trigger"] = "click"

        if self.show_created_by:
            self.fields["created_by"].queryset = User.todos.filter(
                campaign_id=self.user.campaign_id
            )
        else:
            self.fields["created_by"].disabled = True

    @property
    def show_created_by(self):
        return self.user.role.get_scope("process") == SCOPE_CAMPAIGN


class AudioReportSearchForm(BaseSearchForm):
    template_name = "analytics/audioreport/search_form.html"

    created_by = forms.ModelChoiceField(
        required=False,
        label="Creado por",
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label=TODOS_STR,
    )
    not_running = forms.BooleanField(
        required=False,
        label="Excluir Procesos en curso",
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    agent = forms.ModelChoiceField(
        required=False,
        label="Asesor",
        queryset=Agent.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label=TODOS_STR,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["not_running"].widget.attrs["hx-trigger"] = "click"
        self.fields["agent"].queryset = Agent.objects.filter(campaign=self.user.campaign)
        if self.show_created_by:
            self.fields["created_by"].queryset = User.todos.filter(campaign=self.user.campaign)
        else:
            self.fields["created_by"].disabled = True

    @property
    def show_created_by(self):
        return self.user.role.get_scope("process") == SCOPE_CAMPAIGN


class ProcessResultSearchForm(AudioReportSearchForm):
    template_name = "analytics/processresult/search_form.html"

    state = forms.ChoiceField(
        required=False,
        label="Estado",
        choices=complete_todos_choices(get_search_process_result_state_choices()),
        initial=TODOS,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class AnalyticImportSearchForm(BaseSearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["param"].widget.attrs["hx-trigger"] += ", ObjectsImportedRelated from:body"


class AnalyticImportForm(ImportForm):
    name = forms.CharField(label="Nombre", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["class"] += " mb-3"
