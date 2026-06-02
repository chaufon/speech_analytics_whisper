import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Download the Hugging Face model 'pyannote/speaker-diarization-community-1' into "
        "settings.PYANNOTE_MODEL_PATH. Skips if already present unless --force is used."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            dest="force",
            help="Delete existing folder and download again.",
        )

    def handle(self, *args, **options):
        repo_id = "pyannote/speaker-diarization-community-1"
        target_dir = settings.PYANNOTE_MODEL_PATH
        force = bool(options.get("force"))
        hf_token = os.environ.get("HF_TOKEN")

        # Check existing content
        if target_dir.exists():
            try:
                has_content = any(target_dir.iterdir())
            except Exception as e:
                self.stdout.write(
                    self.style.NOTICE(
                        f"We do not know if target_dir ({target_dir}) already has content: {e}"
                    )
                )
                has_content = True  # be conservative

            if has_content and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"Model directory already exists and is non-empty: {target_dir}. "
                        f"Skipping download."
                    )
                )
                return

            if force:
                self.stdout.write(self.style.NOTICE(f"Removing existing directory: {target_dir}"))
                try:
                    shutil.rmtree(target_dir)
                except Exception as e:
                    raise CommandError(f"Failed to remove existing directory {target_dir}: {e}")

        target_dir.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent exists

        try:
            from huggingface_hub import snapshot_download

            resolved_path = snapshot_download(repo_id=repo_id, token=hf_token, local_dir=target_dir)
        except Exception as e:
            raise CommandError(f"Error downloading model from Hugging Face: {e}")
        else:
            self.stdout.write(self.style.SUCCESS(f"Model downloaded to: {resolved_path}"))
