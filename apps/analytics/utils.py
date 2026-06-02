import os
import subprocess
import tempfile
import uuid
import zipfile

from django.core.files.base import ContentFile
from django.utils import timezone

from pydub import AudioSegment as PydubAudioSegment

from apps.common.constants import (
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
    SCOPE_CAMPAIGN,
    SCOPE_GLOBAL,
    SCOPE_NONE,
    SCOPE_USER,
    SEARCH_PROCESS_RESULT_ERROR,
    SEARCH_PROCESS_RESULT_MATCH,
    SEARCH_PROCESS_RESULT_NO_MATCH,
    SEARCH_PROCESS_STATE_FINISHED,
    SEARCH_PROCESS_STATE_NO_AUDIOS,
    SEARCH_PROCESS_STATE_READY,
    SEARCH_PROCESS_STATE_TRANSCRIBED,
)


def get_new_name_audio_folder(instance, filename):  # NOQA
    instance.original_filename = filename
    new_name = f"{uuid.uuid4().hex}.{filename.split('.')[-1]}"
    return f"{instance.campaign_id}/{timezone.now().strftime('%Y/%m/%d')}/{new_name}".lower()


def get_audio_folder(instance, filename):  # NOQA
    return f"{instance.campaign_id}/{timezone.now().strftime('%Y/%m/%d')}/{filename}".lower()


def get_process_states() -> dict[int, str]:
    return {
        PROCESS_STATE_NO_AUDIOS: "Sin audios",
        PROCESS_STATE_READY: "Listo para procesar",
        PROCESS_STATE_TRANSCRIBED: "Transcripción de audios finalizada",
        PROCESS_STATE_TRANSCRIBED_PARTIAL: "Transcripción de audios parcial",
        PROCESS_STATE_FINISHED: "Proceso finalizado",
        PROCESS_STATE_FINISHED_PARTIAL: "Proceso parcialmente finalizado",
    }


def get_scopes(allow_user=True, allow_global=True) -> dict[int, str]:
    scopes = {SCOPE_NONE: "Ninguno"}
    if allow_user:
        scopes.update({SCOPE_USER: "Solo los creados por el usuario"})
    scopes.update({SCOPE_CAMPAIGN: "Los de la campaña"})
    if allow_global:
        scopes.update({SCOPE_GLOBAL: "De todas las campañas"})
    return scopes


def process_restart_extra() -> dict[int, str]:
    return {
        RESTART_EXTRA_FULL: "Reprocesar todo",
        RESTART_EXTRA_PARTIAL: "Volver a tipificar",
        RESTART_EXTRA_RESET_TYPIFY: "Reset antes de tipificar",
        RESTART_EXTRA_RESET_NEW: "Reset antes de transcribir",
    }


def get_process_result_states() -> dict[int, str]:
    return {
        PROCESS_RESULT_MATCH: "Se encontró coincidencia",
        PROCESS_RESULT_NO_MATCH: "NO se encontró coincidencia",
        PROCESS_RESULT_ERROR: "Error en la consulta",
    }


def get_search_process_state_choices() -> tuple:
    return (
        (SEARCH_PROCESS_STATE_NO_AUDIOS, get_process_states()[PROCESS_STATE_NO_AUDIOS].upper()),
        (SEARCH_PROCESS_STATE_READY, get_process_states()[PROCESS_STATE_READY].upper()),
        (SEARCH_PROCESS_STATE_TRANSCRIBED, get_process_states()[PROCESS_STATE_TRANSCRIBED].upper()),
        (SEARCH_PROCESS_STATE_FINISHED, get_process_states()[PROCESS_STATE_FINISHED].upper()),
    )


def get_search_process_result_state_choices() -> tuple:
    return (
        (SEARCH_PROCESS_RESULT_MATCH, get_process_result_states()[PROCESS_RESULT_MATCH].upper()),
        (
            SEARCH_PROCESS_RESULT_NO_MATCH,
            get_process_result_states()[PROCESS_RESULT_NO_MATCH].upper(),
        ),
        (SEARCH_PROCESS_RESULT_ERROR, get_process_result_states()[PROCESS_RESULT_ERROR].upper()),
    )


def is_zip(file) -> bool:
    result = zipfile.is_zipfile(file)
    file.seek(0)
    return result


def is_v3(file) -> bool:
    return file.name.lower().endswith(".v3")


def is_wav(file):
    try:
        _ = PydubAudioSegment.from_wav(file)
        return True
    except Exception:  # NOQA
        return False


def convert_wav_to_mp3(file):
    content_file = None
    original_name = file.name
    base_name = os.path.splitext(original_name)[0]
    output_name = base_name + ".mp3"
    try:
        audio = PydubAudioSegment.from_wav(file)
        # Export as MP3
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_output:
            tmp_output_path = tmp_output.name
            audio.export(tmp_output_path, format="mp3")

            content_file = ContentFile(open(tmp_output_path, "rb").read(), name=output_name)
            os.unlink(tmp_output_path)
    except Exception:  # NOQA
        raise
    else:
        return content_file


def convert_v3_to_mp3(file):
    content_file = None
    original_name = file.name
    base_name = os.path.splitext(original_name)[0]
    output_name = base_name + ".mp3"
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_input_path = os.path.join(tmp_dir, original_name)
            with open(tmp_input_path, "wb+") as tmp_input_file:
                for chunk in file.chunks():
                    tmp_input_file.write(chunk)

            tmp_output_path = os.path.join(tmp_dir, output_name)

            sox_command = [
                "sox",
                "-t",
                "vox",
                "-r",
                "6000",
                "-c",
                "1",
                tmp_input_path,
                "-r",
                "16000",
                tmp_output_path,
            ]

            _ = subprocess.run(sox_command, capture_output=True, text=True, check=True)
            content_file = ContentFile(open(tmp_output_path, "rb").read(), name=output_name)
    except Exception:  # NOQA
        raise
    else:
        return content_file


def get_process_types() -> tuple:
    return (PROCESS_TYPE_AWS, "AWS"), (PROCESS_TYPE_LOCAL, "LOCAL")


def get_duration_from_audio(audio_file):
    pydub_audio_segment = PydubAudioSegment.from_file(audio_file)
    return int(pydub_audio_segment.duration_seconds)
