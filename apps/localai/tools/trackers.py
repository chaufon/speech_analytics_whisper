import logging
import os
import subprocess
import threading
import time

import psutil

logger = logging.getLogger(__name__)


class PeakResourceTracker:
    def __init__(self, interval: float = 0.1):
        self.interval = interval
        self._stop = threading.Event()
        self._thread = None
        self.peak_total_vram = 0
        self.peak_self_ram = 0
        self.peak_self_cpu = 0.0
        self.peak_total_gpu = 0

    def _run(self):
        while not self._stop.is_set():
            try:
                self._update_peak_stats()
            except Exception as e:
                logger.error(f"Error updating peak stats in tracker: {e}")
                self.peak_total_vram = 0
                self.peak_self_ram = 0
                self.peak_self_cpu = 0.0
                self.peak_total_gpu = 0
                break
            else:
                time.sleep(self.interval)

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def _update_peak_stats(self):
        self._get_current_total_vram_used()
        self._get_current_total_gpu_used()
        self._get_current_self_ram_used()
        self._get_current_self_cpu_used()

    def _get_current_total_vram_used(self) -> None:
        out = subprocess.check_output(
            ["nvidia-smi", "--id=0", "--query-gpu=memory.used", "--format=csv,nounits,noheader"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        current_total_vram_used = int(out.splitlines()[0].strip())
        self.peak_total_vram = max(self.peak_total_vram, current_total_vram_used)

    def _get_current_total_gpu_used(self) -> None:
        """Total GPU utilization percentage (0-100)."""
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--id=0",
                "--query-gpu=utilization.gpu",
                "--format=csv,nounits,noheader",
            ],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        current_total_gpu_used = int(out.splitlines()[0].strip())
        self.peak_total_gpu = max(self.peak_total_gpu, current_total_gpu_used)

    def _get_current_self_ram_used(self) -> None:
        """Return current process RAM usage in MB."""
        process = psutil.Process(os.getpid())
        # rss = resident set size (real memory in use)
        current_self_ram_used = process.memory_info().rss // (1024 * 1024)
        self.peak_self_ram = max(self.peak_self_ram, current_self_ram_used)

    def _get_current_self_cpu_used(self) -> None:
        """Return current process CPU usage percentage."""
        process = psutil.Process(os.getpid())
        cpu_used = float(process.cpu_percent(interval=None))
        self.peak_self_cpu = max(self.peak_self_cpu, cpu_used)


def get_queue_stats() -> dict:
    from django.conf import settings

    from celery import current_app

    queue_stats = dict()

    def _process_inspect(active: bool = True) -> dict:
        processed = dict()
        total_tasks = inspect.active() if active else inspect.reserved()
        for worker, tasks in total_tasks.items():
            if settings.LOCALAI_CPU_QUEUE in worker:
                processed[settings.LOCALAI_CPU_QUEUE] = len(tasks)
            elif settings.LOCALAI_CUDA_QUEUE in worker:
                processed[settings.LOCALAI_CUDA_QUEUE] = len(tasks)
        return processed

    try:
        inspect = current_app.control.inspect()
    except Exception as e:
        logger.error(f"Error trying to access celery statistics: {e}")
    else:
        queue_stats["active"] = _process_inspect(active=True)
        queue_stats["reserved"] = _process_inspect(active=False)

    return queue_stats
