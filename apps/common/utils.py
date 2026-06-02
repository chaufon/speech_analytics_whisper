from apps.common.constants import LOCALAI_MODE_PERFORMANCE, LOCALAI_MODE_QUALITY


def get_localai_modes() -> tuple[tuple[int, str], ...]:
    return (LOCALAI_MODE_QUALITY, "Calidad"), (LOCALAI_MODE_PERFORMANCE, "Performance")
