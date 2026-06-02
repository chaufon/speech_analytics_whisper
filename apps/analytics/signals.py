import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.analytics.models import Audio

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Audio)
def update_process_state(sender, instance, **kwargs):
    """
    Signal to update the process state when an Audio instance is saved.
    """
    process = instance.process
    if not process.is_running:
        process.update_state(instance.modify_user)
