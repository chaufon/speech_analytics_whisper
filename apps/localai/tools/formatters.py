def aws_formatter(transcription_segments: list, diarization_segments: list) -> dict:
    transcription = {
        "jobName": "EXAMPLE-0000000000",
        "accountId": "000000000000",
        "status": "COMPLETED",
        "results": {
            "transcripts": [
                {
                    "transcript": "Hola buenos d\u00edas, le saluda un asesor del Operator."
                }
            ],
            "speaker_labels": {
                "segments": [
                    {
                        "start_time": "1.379",
                        "end_time": "7.409",
                        "speaker_label": "spk_0",
                        "items": [
                            {"speaker_label": "spk_0", "start_time": "1.44", "end_time": "1.46"},
                            {"speaker_label": "spk_0", "start_time": "2.66", "end_time": "2.9"},
                            {"speaker_label": "spk_0", "start_time": "3.019", "end_time": "3.339"},
                            {"speaker_label": "spk_0", "start_time": "6.94", "end_time": "7.26"},
                        ],
                    },
                    {
                        "start_time": "9.43",
                        "end_time": "10.989",
                        "speaker_label": "spk_1",
                        "items": [
                            {"speaker_label": "spk_1", "start_time": "9.59", "end_time": "9.789"},
                            {"speaker_label": "spk_1", "start_time": "9.909", "end_time": "10.109"},
                            {
                                "speaker_label": "spk_1",
                                "start_time": "10.109",
                                "end_time": "10.369",
                            },
                            {"speaker_label": "spk_1", "start_time": "10.43", "end_time": "10.989"},
                        ],
                    },
                ],
                "channel_label": "ch_0",
                "speakers": 2,
            },
            "items": [
                {
                    "id": 0,
                    "type": "pronunciation",
                    "alternatives": [{"confidence": "0.525", "content": "Al\u00f3"}],
                    "start_time": "1.44",
                    "end_time": "1.46",
                    "speaker_label": "spk_0",
                },
                {
                    "id": 1,
                    "type": "pronunciation",
                    "alternatives": [{"confidence": "0.959", "content": "Hola"}],
                    "start_time": "2.66",
                    "end_time": "2.9",
                    "speaker_label": "spk_0",
                },
                {
                    "id": 587,
                    "type": "punctuation",
                    "alternatives": [{"confidence": "0.0", "content": "."}],
                    "speaker_label": "spk_0",
                },
            ],
            "audio_segments": [
                {
                    "id": 0,
                    "transcript": "Hola buenos d\u00edas, le saluda un asesor del Operator.",  # NOQA
                    "start_time": "1.379",
                    "end_time": "7.409",
                    "speaker_label": "spk_0",
                    "items": [
                        0,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                        20,
                        21,
                    ],
                }
            ],
        },
    }
    audio_segments = list()
    counter = 1
    transcript = ""

    for transcription_segment in transcription_segments:
        best_match = None
        max_overlap = 0

        for diarization_segment in diarization_segments:
            overlap_start = max(transcription_segment["start_time"], diarization_segment["start"])
            overlap_end = min(transcription_segment["end_time"], diarization_segment["end"])
            overlap = max(0, overlap_end - overlap_start)

            if overlap > max_overlap:
                max_overlap = overlap
                best_match = diarization_segment

        # TODO integrate midpoint match maybe
        speaker_label = best_match["speaker"] if best_match else "SPEAKER99"

        transcription_segment["speaker_label"] = speaker_label
        transcription_segment["id"] = counter

        transcript += transcription_segment["transcript"]
        counter += 1

        audio_segments.append(transcription_segment)

    transcription["results"]["transcripts"][0]["transcript"] = transcript
    transcription["results"]["audio_segments"] = audio_segments
    transcription["results"]["transcription_segments"] = transcription_segments
    transcription["results"]["diarization_segments"] = diarization_segments

    return transcription


def get_clip_timestamps(diarization_segments: list) -> str:
    clip_timestamps = ""
    for segment in diarization_segments:
        start = float(segment["start"])
        end = float(segment["end"])
        clip_timestamps += f"{start:.2f},{end:.2f},"
    return clip_timestamps.removesuffix(",")
