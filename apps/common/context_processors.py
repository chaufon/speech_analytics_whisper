from maintenance.constants import MENU_MANTENIMIENTOS

from apps.common.constants import (
    API_ACTION_CONTINUE,
    API_ACTION_MAIN,
    API_ACTION_PAUSE,
    API_ACTION_RESTART,
    API_ACTION_START,
    MENU_PROCESS,
    MENU_RESULT,
)


def menu(request):  # NOQA
    return {
        "menu": {
            "mantenimientos": MENU_MANTENIMIENTOS,
            "process": MENU_PROCESS,
            "result": MENU_RESULT,
        },
        "process": {
            "main": API_ACTION_MAIN,
            "start": API_ACTION_START,
            "pause": API_ACTION_PAUSE,
            "continue": API_ACTION_CONTINUE,
            "restart": API_ACTION_RESTART,
        },
    }
