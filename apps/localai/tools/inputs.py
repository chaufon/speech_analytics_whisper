from dataclasses import asdict, dataclass


@dataclass
class InputBase:
    device: str
    model: str
    compute_type: str
    beam_size: int
    track_memory: bool

    def as_dict(self):
        return asdict(self)


@dataclass
class InputFasterWhisper(InputBase):
    audio_path: str
    clip_timestamps: str


@dataclass
class InputTranscribe(InputBase):
    audio_pk: int
    user_pk: int
