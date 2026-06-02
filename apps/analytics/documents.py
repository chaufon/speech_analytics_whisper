from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from apps.analytics.models import AudioSegment


@registry.register_document
class AudioSegmentDocument(Document):
    text = fields.TextField(analyzer="spanish")
    audio_id = fields.IntegerField()

    class Index:
        name = "audiosegment"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = AudioSegment
        fields = ("id", "speaker_label")
