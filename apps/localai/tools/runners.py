import logging
import time

from django.conf import settings

from apps.common.exceptions import BaseAnalyticsException
from apps.localai.tools.inputs import InputFasterWhisper
from apps.localai.tools.trackers import PeakResourceTracker

logger = logging.getLogger(__name__)


class IALocalModelLoading(BaseAnalyticsException):
    msg = "Error al cargar el modelo IA Local"


class IALocalTranscriptionError(BaseAnalyticsException):
    msg = "Error al transcribir usando IA Local"


class IALocalDiarizationModelLoading(BaseAnalyticsException):
    msg = "Error al cargar el modelo para identificar speakers usando IA Local"


class IALocalDiarizationError(BaseAnalyticsException):
    msg = "Error al identificar speakers usando IA Local"


def clean_model(model_object):  # NOQA
    import gc

    import torch

    del model_object
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()  # TODO check if it has some effect on 5090 (none on 3060)
    gc.collect()


def run_faster_whisper(**kwargs) -> tuple[list, dict]:
    from faster_whisper import WhisperModel

    initial_prompt = (
        "Esta conversación se da entre un asesor comercial de la empresa Operator y un cliente "
        "interesado en adquirir un nuevo plan para sus llamadas a celular, paquete de datos y sms. "
        "Ejemplo: Buenas tardes, mi nombre es Juan Perez y llamo de Operator. "
        "Me comunico con el Sr. Jane Doe con DNI 00000000 y número celular 900000000. Le ofrezco "
        "un plan de 60 GB de Internet y una renta mensual de 59.90 soles."
    )
    hotwords = "DNI, Operator"
    language = "es"
    transcription_stats = dict()
    input_faster = InputFasterWhisper(**kwargs)

    start = time.time()
    try:
        model = WhisperModel(
            input_faster.model,
            device=input_faster.device,
            compute_type=input_faster.compute_type,
            local_files_only=True,
            use_auth_token=None,
        )
    except Exception as e:  # NOQA
        print("error: ", e, str(e))
        try:
            model = WhisperModel(
                input_faster.model,
                device=input_faster.device,
                compute_type=input_faster.compute_type,
                local_files_only=False,  # maybe the model hasn't been downloaded yet
            )
        except Exception as e:
            logger.error(f"Error loading IA Local: {e}")
            raise IALocalModelLoading()
        else:
            logger.info(f"Model {input_faster.model} downloaded successfully")

    tracker = PeakResourceTracker()
    tracker.start()

    segments, info = model.transcribe(
        input_faster.audio_path,
        beam_size=input_faster.beam_size,
        language=language,
        initial_prompt=initial_prompt,
        prefix=None,
        hotwords=hotwords,
        condition_on_previous_text=True,
    )

    transcription_segments = list()

    try:
        for segment in segments:  # segments is an iterator
            transcription_segments.append(
                {"transcript": segment.text, "start_time": segment.start, "end_time": segment.end}
            )
    except Exception as e:
        logger.error(f"Error formatting transcription: {e}")
        raise IALocalTranscriptionError()
    else:
        tracker.stop()
        end = time.time()

        transcription_stats["duration_audio"] = info.duration
        transcription_stats["duration_transcription"] = f"{end - start:.2f}"
        transcription_stats["peak_total_vram"] = tracker.peak_total_vram
        transcription_stats["peak_total_gpu"] = tracker.peak_total_gpu
        transcription_stats["peak_self_ram"] = tracker.peak_self_ram
        transcription_stats["peak_self_cpu"] = tracker.peak_self_cpu

        return transcription_segments, transcription_stats
    finally:
        clean_model(model)


def run_diarization(audio_path: str, device: str) -> list:
    import torch
    from pyannote.audio import Pipeline

    num_speakers = 2
    diarization_segments = list()

    # PyTorch >=2.6 defaults torch.load(weights_only=True), which rejects the
    # pyannote checkpoint globals. The checkpoint is downloaded from the official
    # HuggingFace repo by our own management command, so we force weights_only=False.
    original_torch_load = torch.load

    def trusted_torch_load(*args, **kwargs):
        kwargs["weights_only"] = False
        return original_torch_load(*args, **kwargs)

    try:
        torch.load = trusted_torch_load
        try:
            pipeline = Pipeline.from_pretrained(settings.PYANNOTE_MODEL_PATH, cache_dir=None)
        finally:
            torch.load = original_torch_load
    except Exception as e:
        logger.error(f"Error loading diarization model: {e}")
        raise IALocalDiarizationModelLoading()

    try:
        pipeline.to(torch.device(device))

        diarization = pipeline(audio_path, num_speakers=num_speakers)
    except Exception as e:
        logger.error(f"Error loading diarization model: {e}")
        raise IALocalDiarizationError()
    else:
        for turn, speaker in diarization.speaker_diarization:
            diarization_segments.append({"start": turn.start, "end": turn.end, "speaker": speaker})

        return diarization_segments
    finally:
        clean_model(pipeline)
