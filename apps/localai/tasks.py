import logging

from celery import shared_task

from apps.analytics.control import Control
from apps.analytics.models import Audio
from apps.common.models import Config
from apps.localai.tools.formatters import aws_formatter, get_clip_timestamps
from apps.localai.tools.runners import (
    IALocalModelLoading,
    IALocalTranscriptionError,
    run_diarization,
)
from apps.users.models import User

logger = logging.getLogger(__name__)


def transcribe_audio(**kwargs) -> None:
    transcription = None
    audio_pk = kwargs.pop("audio_pk")
    user_pk = kwargs.pop("user_pk")
    device = kwargs.get("device")
    error = ""

    audio = Audio.objects.get(pk=audio_pk)
    user = User.objects.get(pk=user_pk)
    slow_down_factor = Config.objects.first().slow_down_factor

    if Control(audio.process_id).is_paused:
        audio.save_transcription_completed(transcription, user, slow_down_factor)
        return

    from apps.localai.tools.runners import run_faster_whisper

    kwargs["audio_path"] = audio.file.path

    try:
        audio.convert_to_wav()
        diarization_segments = run_diarization(audio.wav_temp_path, device=device)
    except Exception as e:
        logger.error(f"Error on diarization of audio {audio.pk} con {device}: {e}")
        error = f"Error al identificar participantes usando ({device})"
        audio.save_transcription_completed(transcription, user, slow_down_factor, error)
        raise
    else:
        clip_timestamps = get_clip_timestamps(diarization_segments)
    finally:
        audio.clean_wav_temp_path()

    if Control(audio.process_id).is_paused:
        audio.save_transcription_completed(transcription, user, slow_down_factor)
        return

    kwargs["clip_timestamps"] = clip_timestamps

    try:
        transcription_segments, transcription_stats = run_faster_whisper(**kwargs)
    except (IALocalModelLoading, IALocalTranscriptionError) as e:
        error = str(e)
    except Exception as e:  # NOQA
        logger.error(f"Error transcribing audio {audio.pk} with {device}: {e}")
        error = f"Error desconocido al transcribir usando ({device})"
        raise
    else:  # TODO save it in separate model
        logger.info(f"Transcription statistics for audio {audio.pk}: {transcription_stats}")
        transcription = aws_formatter(transcription_segments, diarization_segments)
    finally:
        audio.save_transcription_completed(transcription, user, slow_down_factor, error)


@shared_task
def launch_transcribe_cuda(**kwargs) -> None:
    transcribe_audio(**kwargs)


@shared_task
def launch_transcribe_cpu(**kwargs) -> None:
    transcribe_audio(**kwargs)
