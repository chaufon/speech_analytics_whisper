from django.core.cache import cache

from apps.common.exceptions import BaseAnalyticsException


class ControlError(Exception):
    pass


class ControlForceStop(BaseAnalyticsException):
    msg = "Pausado manualmente por un usuario"


class Control:
    control_name = "control_pause"
    timeout = 3600

    def __init__(self, process_id: int):
        self.process_id = str(process_id)
        self.pauses = self._get_control_dict()

    def _get_control_dict(self) -> dict:
        try:
            control_dict = cache.get(self.control_name)
            if not control_dict:
                control_dict = dict()
                cache.set(self.control_name, control_dict)
        except Exception as e:
            raise ControlError(f"Error getting control dict: {e}")
        else:
            return control_dict

    def set_pause_process(self, user_id: int) -> None:
        self.pauses.update({self.process_id: str(user_id)})
        try:
            cache.set(self.control_name, self.pauses, self.timeout)
        except Exception as e:
            raise ControlError(f"Error pausing process {self.process_id}: {e}")

    def remove_pause_process(self) -> None:
        _ = self.pauses.pop(self.process_id, None)
        try:
            cache.set(self.control_name, self.pauses)
        except Exception as e:
            raise ControlError(f"Error unpausing process {self.process_id}: {e}")

    def get_user_id(self) -> int | None:
        user_id = self.pauses.get(self.process_id)
        return int(user_id) if user_id else None

    @property
    def is_paused(self) -> bool:
        return self.process_id in self.pauses.keys()
