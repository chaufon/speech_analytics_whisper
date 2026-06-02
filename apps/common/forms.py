from django import forms

from maintenance.forms import MaintenanceBaseModelForm, SearchForm

from apps.common.constants import AUDIO_SLOWDOWN_FACTOR_MAX, AUDIO_SLOWDOWN_FACTOR_MIN
from apps.common.models import Config


class BaseSearchForm(SearchForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_multi_filter:
            self.fields["param"].label = "Nombre"

        hx_get = self.fields["param"].widget.attrs["hx-get"]

        for field in self.fields:
            if field != "param":
                self.fields[field].widget.attrs["hx-trigger"] = "change"
                self.fields[field].widget.attrs["hx-get"] = hx_get
                self.fields[field].widget.attrs["hx-target"] = "#search-results"
                self.fields[field].widget.attrs["hx-indicator"] = "#search-indicator"
                self.fields[field].widget.attrs["hx-swap"] = "outerHTML"
                self.fields[field].widget.attrs["hx-include"] = "#search-filters"
                self.fields[field].widget.attrs["autocomplete"] = "off"

    @property
    def is_multi_filter(self):
        return len(self.fields) > 1


class ConfigEditForm(MaintenanceBaseModelForm):
    template_name = "common/config/edit_form.html"

    class Meta:
        model = Config
        fields = (
            "audios_slow_down_enable",
            "audios_slow_down_factor",
            "process_list_refresh",
            "transcribe_get_results_max_tries",
            "transcribe_get_results_seconds_between",
            "localai_mode",
            "localai_use_cpu",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audios_slow_down_factor"].widget.attrs.update(
            {
                "min": str(AUDIO_SLOWDOWN_FACTOR_MIN),
                "max": str(AUDIO_SLOWDOWN_FACTOR_MAX),
                "step": str(0.01),
            }
        )

    def clean_audios_slow_down_factor(self):
        audios_slow_down_factor = self.cleaned_data["audios_slow_down_factor"]
        if not (AUDIO_SLOWDOWN_FACTOR_MIN <= audios_slow_down_factor <= AUDIO_SLOWDOWN_FACTOR_MAX):
            raise forms.ValidationError(
                "El factor de retraso de audios debe estar entre 0.8 y 0.95"
            )
        return audios_slow_down_factor
