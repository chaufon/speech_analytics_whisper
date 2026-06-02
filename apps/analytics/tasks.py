import logging

from celery import shared_task

from apps.analytics.models import Process
from apps.analytics.processors import Analyzer
from apps.users.models import User

logger = logging.getLogger(__name__)


@shared_task()
def launch_analyzer_task(process_pk: int, user_pk: int):
    try:
        process = Process.objects.select_related("wordlist").get(pk=process_pk)
        user = User.objects.get(pk=user_pk)
    except Process.DoesNotExist:
        logger.error(f"Process {process_pk} does not exist")
        return
    except User.DoesNotExist:
        logger.error(f"User {user_pk} does not exist")
    else:
        Analyzer(process, user).run()
