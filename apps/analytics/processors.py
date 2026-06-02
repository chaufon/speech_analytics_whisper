import copy
import logging
import os
import time

from django.conf import settings
from django.utils import timezone

import boto3
import requests
from elasticsearch.dsl import Q

from apps.analytics.control import Control, ControlForceStop
from apps.analytics.documents import AudioSegmentDocument
from apps.analytics.models import ProcessResult
from apps.common.constants import PROCESS_RESULT_ERROR, PROCESS_RESULT_MATCH
from apps.common.exceptions import BaseAnalyticsException
from apps.common.models import Config
from apps.users.models import User

logger = logging.getLogger(__name__)


class TranscribeError(BaseAnalyticsException):
    msg = "Error transcribiendo audios. No se ha completado la tarea."


class TypifyError(BaseAnalyticsException):
    msg = "Error tipificar los audios. No se ha completado la tarea."


class AudioFolderNotMountedError(BaseAnalyticsException):
    msg = "Error con la carpeta de red. No se puede acceder a los audios"


class CeleryNotRunningError(BaseAnalyticsException):
    msg = "Servicio Celery no se encuentra operativo. Se cancela la ejecución del proceso."


class ElasticSearchError(BaseAnalyticsException):
    msg = "Error al conectar con servicio Elasticsearch. Se cancela la ejecución del proceso."


class TasksWithoutResultsTimeOutError(BaseAnalyticsException):
    msg = "Tiempo de espera máximo alcanzado, transcripciones incompletas"


class Analyzer:
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    s3_client = None
    transcribe_client = None
    with_errors = False
    audios = list()

    def __init__(self, process, user):
        self.process = process
        self.user = user
        if self.process.is_aws:
            self.s3_client = self._get_s3_client()
            self.transcribe_client = self._get_transcribe_client()

    @staticmethod
    def _get_transcribe_client():
        return boto3.client(
            "transcribe",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

    @staticmethod
    def _get_s3_client():
        return boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

    def _delete_everything_from_aws(self):
        for audio in self.process.all_audios:
            try:
                self.transcribe_client.delete_transcription_job(
                    TranscriptionJobName=audio.transcribe_job_name
                )
                self.s3_client.delete_object(Bucket=self.bucket, Key=audio.file_str)
            except Exception:  # NOQA
                pass

    def _pause_process(self, user_pk: int | None) -> None:
        responsible_user = None
        if user_pk:
            try:
                responsible_user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                logger.error(f"User {user_pk} does not exist.")
            else:
                self.user = responsible_user
        self.process.set_is_paused(responsible_user)

    def run(self) -> None:  # NOQA
        if self.process.is_empty:
            logger.error(f"Process without audios (pk: {self.process.pk}) was attempted to run.")
            self.process.set_is_not_running(self.user)
            return

        if self.process.is_finished:
            logger.error(f"Process already finished (pk: {self.process.pk}) was attempted to run.")
            self.process.set_is_not_running(self.user)
            return

        operations = [self._transcribe, self._typify]

        if self.process.is_transcribed:
            operations.pop(0)

        if not self.process.is_running:
            self.process.set_is_running(self.user)

        try:
            for operation in operations:
                control = Control(self.process.pk)

                if control.is_paused:
                    raise ControlForceStop()

                operation()
        except ControlForceStop:
            self._pause_process(Control(self.process.pk).get_user_id())
        except (
            AudioFolderNotMountedError,
            TranscribeError,
            TypifyError,
            CeleryNotRunningError,
            ElasticSearchError,
            TasksWithoutResultsTimeOutError,
        ) as e:
            self.process.had_errors = True
            self.process.details = str(e)
        except Exception as e:
            logger.info(f"Error in run: {e}")
            self.process.had_errors = True
            self.process.details = "No se ha completado la operación"
        finally:
            self.process.set_is_not_running(self.user)

            try:
                Control(self.process.pk).remove_pause_process()
            except Exception as e:
                logger.error(f"Error removing pause process: {e}")

            if self.process.is_aws:
                self._delete_everything_from_aws()

    def _transcribe(self):
        if settings.DJANGO_MEDIA_ROOT_IS_MOUNTED and not os.path.ismount(settings.MEDIA_ROOT):
            raise AudioFolderNotMountedError()

        try:
            audios_for_transcription = self.process.get_audios_for_transcription(self.user)
        except Exception as e:
            logger.error(f"Unexpected error while retrieving audios for transcribing: {e}")
            raise TranscribeError()
        else:
            if not audios_for_transcription:
                return

            if self.process.is_aws:
                self._run_aws_transcription(audios_for_transcription)
            else:
                self._run_localai_transcription(audios_for_transcription)

    def _run_localai_transcription(self, audios_cuda: list):
        from apps.localai.tasks import launch_transcribe_cpu, launch_transcribe_cuda
        from apps.localai.tools.inputs import InputTranscribe
        from apps.localai.tools.trackers import get_queue_stats

        config = Config.objects.first()
        stats = get_queue_stats()  # TODO stored permanently
        if not stats:
            raise CeleryNotRunningError()

        logger.info(f"Celery queue stats: {stats}")

        audios_cpu = list()
        audios_len = len(audios_cuda)

        current_reserved_tasks = stats["reserved"][settings.LOCALAI_CUDA_QUEUE]
        if number_to_send_cpu := config.localai_send_to_cpu(current_reserved_tasks, audios_len):
            audios_cpu = copy.deepcopy(audios_cuda)
            if number_to_send_cpu == audios_len:
                audios_cuda = list()
            else:
                audios_cpu = audios_cpu[:number_to_send_cpu]
                audios_cuda = audios_cuda[number_to_send_cpu:]

        task_results = list()
        model = config.model
        track_stats = config.localai_track_stats

        if audios_cuda:
            device = "cuda"
            compute_type, beam_size = config.localai_get_model_params()

            for audio in audios_cuda:
                transcribe_input = InputTranscribe(
                    device=device,
                    model=model,
                    compute_type=compute_type,
                    beam_size=beam_size,
                    track_memory=track_stats,
                    audio_pk=audio.pk,
                    user_pk=self.user.pk,
                )
                task = launch_transcribe_cuda.apply_async(
                    kwargs=transcribe_input.as_dict(), routing_key="default"
                )
                task_results.append(task)

        if audios_cpu:
            device = "cpu"
            compute_type, beam_size = config.localai_get_model_params(cuda=False)

            for audio in audios_cpu:
                transcribe_input = InputTranscribe(
                    device=device,
                    model=model,
                    compute_type=compute_type,
                    beam_size=beam_size,
                    track_memory=track_stats,
                    audio_pk=audio.pk,
                    user_pk=self.user.pk,
                )
                task = launch_transcribe_cpu.apply_async(
                    kwargs=transcribe_input.as_dict(), routing_key="default"
                )
                task_results.append(task)

        # check for all tasks to finish
        counter = 0
        while counter < config.localai_get_max_tries:
            if Control(self.process.pk).is_paused:
                raise ControlForceStop()

            counter += 1
            if all(task.ready() for task in task_results):
                break
            time.sleep(config.localai_get_seconds_between)

        if counter >= config.localai_get_max_tries:
            raise TasksWithoutResultsTimeOutError()

        logger.info(f"All tasks finished. Jobs failed: {len([t.failed() for t in task_results])}")

    def _run_aws_transcription(self, audios: list) -> None:
        uploaded_audios = self._aws_upload(audios)

        audios_with_jobs = self._aws_create_jobs(uploaded_audios)

        self._aws_get_results(audios_with_jobs)

    def _aws_get_results(self, audios: list) -> None:
        if audios:
            config = Config.objects.first()
            counter = 0

            while len(audios) > 0 and counter < config.transcribe_get_results_max_tries:
                if Control(self.process.pk).is_paused:
                    raise ControlForceStop()

                for audio in audios:
                    try:
                        response = self.transcribe_client.get_transcription_job(
                            TranscriptionJobName=audio.transcribe_job_name
                        )
                    except Exception as e:
                        logger.error(f"Error fetching transcription of audio {audio.pk}: {e}")
                        audio.save_transcription_completed(
                            transcription=None,
                            user=self.user,
                            slow_down_factor=config.slow_down_factor,
                            error_detail="Error al consultar AWS Transcribe",
                        )
                        audios.remove(audio)
                    else:
                        status = response["TranscriptionJob"]["TranscriptionJobStatus"]
                        logger.info(
                            f"Transcription job {audio.transcribe_job_name} status: {status}"
                        )

                        if status not in ("COMPLETED", "FAILED"):
                            continue

                        transcription = None
                        if status == "COMPLETED":
                            response = requests.get(
                                response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                            )
                            transcription = response.json()

                        audio.save_transcription_completed(
                            transcription, self.user, config.slow_down_factor
                        )
                        audios.remove(audio)

                counter += 1
                time.sleep(config.transcribe_get_results_seconds_between)

    def _aws_create_jobs(self, audios: list) -> list:
        audios_with_jobs = list()

        if audios:
            if Control(self.process.pk).is_paused:
                raise ControlForceStop()

            config = Config.objects.first()
            for audio in audios:
                try:
                    self.transcribe_client.start_transcription_job(
                        TranscriptionJobName=audio.transcribe_job_name,
                        Media={"MediaFileUri": audio.s3_uri(self.bucket)},
                        MediaFormat=audio.extension_str,
                        LanguageCode="es-US",
                        Settings={"ShowSpeakerLabels": True, "MaxSpeakerLabels": 2},
                    )
                except Exception as e:
                    logger.error(f"Error creating aws job to audio {audio.pk}: {e}")
                    audio.save_transcription_completed(
                        transcription=None,
                        user=self.user,
                        slow_down_factor=config.slow_down_factor,
                        error_detail="Error al crear AWS job",
                    )
                else:
                    audios_with_jobs.append(audio)
        return audios_with_jobs

    def _aws_upload(self, audios: list) -> list:
        uploaded_audios = list()

        if audios:
            config = Config.objects.first()

            for audio in audios:
                audio_to_upload_path = audio.file.path
                try:
                    if config.audios_slow_down_enable:
                        audio.slow_down(config.audios_slow_down_factor)
                        audio_to_upload_path = audio.slow_temp_path
                    self.s3_client.upload_file(audio_to_upload_path, self.bucket, audio.file_str)
                except Exception as e:
                    logger.error(f"Error uploading audio {audio.pk} to S3: {e}")
                    audio.save_transcription_completed(
                        transcription=None,
                        user=self.user,
                        slow_down_factor=config.slow_down_factor,
                        error_detail="Error al subir los audios a AWS S3",
                    )
                else:
                    uploaded_audios.append(audio)
                finally:
                    if config.audios_slow_down_enable:
                        audio.clean_slow_temp_path()
        return uploaded_audios

    def _typify(self):
        try:
            audios_to_typify = self.process.get_audios_to_typify(self.user)
        except Exception as e:
            logger.error(f"Unexpected error while retrieving audios for Typifying: {e}")
            raise TypifyError()

        if not audios_to_typify:
            return

        try:
            self.process.create_in_elasticsearch(audios_to_typify)
        except Exception as e:
            logger.error(f"Unexpected error while creating documents in Elasticsearch: {e}")
            raise ElasticSearchError()

        self._typify_get_results(audios_to_typify)

    def _typify_get_results(self, audios: list) -> None:
        error_msg = ""
        process_results_to_create = list()

        for typification in self.process.typifications.prefetch_related("patterns").all():
            should_queries = list()
            patterns = typification.patterns.all()
            for pattern in patterns:
                text = {"query": pattern.cleaned_sentence, "_name": f"pattern_{pattern.pk}"}
                if pattern.is_variable:
                    text.update({"slop": pattern.slop})
                should_queries.append(Q("match_phrase", text=text))

            for audio in audios:
                create_data = {
                    "create_user": self.user,
                    "modify_user": self.user,
                    "campaign": self.user.campaign,
                    "process": self.process,
                    "audio": audio,
                    "agent": audio.agent,
                    "agent_date": audio.agent_date,
                    "typification": typification,
                    "pattern_matched_sentence": "",
                    "audio_segment_text": "",
                    "obs": "",
                }
                query = Q(
                    "bool",
                    filter=[Q("term", audio_id=audio.pk)],
                    should=should_queries,
                    minimum_should_match=1,
                )
                try:
                    results = AudioSegmentDocument.search().query(query).execute()
                except Exception as e:
                    error_detail = ", ".join(e.messages) if hasattr(e, "messages") else str(e)
                    error_msg += (
                        f"Error executing search with audio {audio.pk} and typification: "
                        f"{typification}: {error_detail}\n"
                    )
                    create_data.update({"state": PROCESS_RESULT_ERROR})
                else:
                    total_hits = len(results.hits)
                    obs = ""
                    if total_hits:
                        match = results.hits[0]

                        if total_hits > 1:
                            obs = (
                                f"La tipificación obtuvo más de una coincidencia "
                                f"({total_hits} en total). Se escogió la primera.\n\n"
                            )
                            for i in range(total_hits - 1):
                                hit = results.hits[i]
                                pattern_id = int(
                                    hit.meta.matched_queries[0].removeprefix("pattern_")
                                )
                                sentence = [p for p in patterns if p.pk == pattern_id][
                                    0
                                ].cleaned_sentence
                                obs += (
                                    f"{i + 1}. Transcripción: '{hit.text}', hizo match con "
                                    f"oración: '{sentence}', con un score interno: "
                                    f"{hit.meta.score}).\n"
                                )

                        pattern_matched_total = len(match.meta.matched_queries)
                        pattern_matched_id = int(
                            match.meta.matched_queries[0].removeprefix("pattern_")
                        )
                        pattern_matched_sentence = [
                            p for p in patterns if p.pk == pattern_matched_id
                        ][0].cleaned_sentence
                        if pattern_matched_total > 1:
                            obs += (
                                f"La transcripción seleccionada hizo match con más de una "
                                f"oración ({pattern_matched_total} en total). "
                                f"Se escogió la primera.\n\n"
                            )
                            for i in range(pattern_matched_total - 1):
                                pattern_id = int(
                                    match.meta.matched_queries[i].removeprefix("pattern_")
                                )
                                sentence = [p for p in patterns if p.pk == pattern_id][
                                    0
                                ].cleaned_sentence
                                obs += f"{i + 1}. Hizo match con oración '{sentence}'.\n"

                        create_data.update(
                            {
                                "pattern_matched_id": pattern_matched_id,
                                "pattern_matched_sentence": pattern_matched_sentence,
                                "audio_segment_id": match.id,
                                "audio_segment_text": match.text,
                                "state": PROCESS_RESULT_MATCH,
                                "score": match.meta.score,
                                "obs": obs,
                            }
                        )
                finally:
                    now = timezone.now()
                    create_data.update({"create_date": now, "modify_date": now})
                    process_results_to_create.append(ProcessResult(**create_data))

        _ = ProcessResult.objects.bulk_create(process_results_to_create)

        if error_msg:
            logger.error(f"Error querying documents in Elasticsearch: {error_msg}")
