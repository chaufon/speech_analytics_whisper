from django.core.exceptions import ValidationError
from django.db import models

import pghistory
from maintenance.models import BaseCatalogo

from apps.common.constants import (
    AUDIO_SLOWDOWN_FACTOR_MAX,
    AUDIO_SLOWDOWN_FACTOR_MIN,
    LOCALAI_MODE_QUALITY,
)
from apps.common.utils import get_localai_modes


@pghistory.track()
class Config(BaseCatalogo):
    name = None
    is_active = None

    audios_slow_down_enable = models.BooleanField(
        "Habilitar disminuir velocidad de audios", default=False
    )
    audios_slow_down_factor = models.FloatField(
        "Factor disminuir velocidad de audios",
        default=0.95,
        help_text=f"Mínimo {AUDIO_SLOWDOWN_FACTOR_MIN}, máximo {AUDIO_SLOWDOWN_FACTOR_MAX}",
    )
    process_list_refresh = models.PositiveSmallIntegerField("Refresco Lista de Procesos", default=5)
    transcribe_get_results_max_tries = models.PositiveSmallIntegerField(
        "AWS máximo de intentos", default=200
    )
    transcribe_get_results_seconds_between = models.PositiveSmallIntegerField(
        "AWS segundos entre intentos", default=10
    )

    localai_mode = models.PositiveSmallIntegerField(
        "IA Local modo",
        choices=get_localai_modes,
        default=LOCALAI_MODE_QUALITY,
        help_text="<ul><li>Calidad -> mejores transcripciones.</li><li>Performance -> incrementa "
        "la velocidad de "
        "transcripción, sacrificando ligeramente la calidad</li></ul>",
    )
    localai_use_cpu = models.BooleanField(
        "IA Local usar CPU",
        default=False,
        help_text="<ul><li>Solo en casos de elevada carga, asignar tareas de transcripción a la "
        "CPU.</li><li>Utilizará el mismo modo que las GPU</li></ul>",
    )
    localai_get_max_tries = models.PositiveSmallIntegerField(
        "IA Local máximo intentos", default=1000
    )
    localai_get_seconds_between = models.PositiveSmallIntegerField(
        "IA Local segundos entre intentos", default=10
    )
    localai_track_stats = models.BooleanField("Recolectar estadísticas", default=True)
    comment = models.TextField("Comentarios", blank=True)

    GPU_CPU_FACTOR = 10
    CUDA_QUALITY_MAX_TASKS = 12
    CUDA_PERFORMANCE_MAX_TASKS = 20
    CPU_MAX_TASKS = 6

    CUDA_QUALITY_TYPE = "float16"
    CUDA_PERFORMANCE_TYPE = "int8_float16"
    CPU_QUALITY_TYPE = "int16"
    CPU_PERFORMANCE_TYPE = "int8"

    CUDA_CPU_QUALITY_BEAM = 5
    CUDA_CPU_PERFORMANCE_BEAM = 4

    GPU_TRANSCRIBE_MIN_DURATION_FACTOR = 11  # from manual tests

    model = "turbo"

    objects = models.Manager()

    def save(self, *args, **kwargs):
        if self._state.adding and self.__class__.objects.exists():
            raise ValidationError("No se pueden agregar más configuraciones")
        super().save(*args, **kwargs)

    def __str__(self):
        return "Configuración General"

    class Meta:
        verbose_name = "Configuración General"
        verbose_name_plural = "Configuraciones Generales"

    def delete(self):
        raise ValidationError("Prohibido")

    @property
    def localai_is_quality_mode(self):
        return self.localai_mode == LOCALAI_MODE_QUALITY

    def localai_celery_max_tasks(self, cuda: bool = True) -> int:
        return (
            (
                self.CUDA_QUALITY_MAX_TASKS
                if self.localai_is_quality_mode
                else self.CUDA_PERFORMANCE_MAX_TASKS
            )
            if cuda
            else self.CPU_MAX_TASKS
        )

    def localai_send_to_cpu(self, current_reserved_tasks: int, tasks_to_send: int) -> int:
        if current_reserved_tasks == 0:
            return 0

        celery_max_tasks = self.localai_celery_max_tasks()
        if int(current_reserved_tasks / celery_max_tasks) < self.GPU_CPU_FACTOR:
            return 0

        return (
            tasks_to_send - celery_max_tasks if tasks_to_send > celery_max_tasks else tasks_to_send
        )

    def localai_get_model_params(self, cuda: bool = True) -> tuple[str, int]:
        """
        CPU: int16 (5), int8 (4) -> ~2.5GB RAM
        GPU: float16 (5) -> ~1.9GB VRAM, int8_float16 (4) -> ~1.1GB VRAM
        """
        compute_type = (
            (self.CUDA_QUALITY_TYPE if self.localai_is_quality_mode else self.CUDA_PERFORMANCE_TYPE)
            if cuda
            else (
                self.CPU_QUALITY_TYPE if self.localai_is_quality_mode else self.CPU_PERFORMANCE_TYPE
            )
        )

        beam_size = (
            self.CUDA_CPU_QUALITY_BEAM
            if self.localai_is_quality_mode
            else self.CUDA_CPU_PERFORMANCE_BEAM
        )

        return compute_type, beam_size

    @property
    def slow_down_factor(self) -> float | None:
        return self.audios_slow_down_factor if self.audios_slow_down_enable else None

    @property
    def delete_url(self):
        return ""

    @property
    def reactivate_url(self):
        return ""

    @property
    def localai_mode_str(self):
        return self.get_localai_mode_display().upper()

    @property
    def process_list_refresh_str(self):
        return f"Cada {self.process_list_refresh} segundos"
