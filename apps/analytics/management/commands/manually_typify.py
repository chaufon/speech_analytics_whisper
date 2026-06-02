import json
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError

from elasticsearch.dsl import Q

from apps.analytics.documents import AudioSegmentDocument
from apps.analytics.models import Audio, Typification


class Command(BaseCommand):
    help = (
        "Debug Elasticsearch query for an audio using either a typification (its patterns) "
        "or a raw sentence. It only prints results; it doesn't create any DB records."
    )

    def add_arguments(self, parser):
        parser.add_argument("audio_pk", type=int, help="Primary key of Audio to filter by")
        parser.add_argument(
            "--typification-pk",
            type=int,
            dest="typification_pk",
            help="Optional Typification PK to use its patterns as should queries",
        )
        parser.add_argument(
            "--sentence",
            type=str,
            dest="sentence",
            help="Optional plain sentence to search as a single match_phrase",
        )
        parser.add_argument(
            "--explain",
            action="store_true",
            default=False,
            help="Ask Elasticsearch to include scoring explanations (can be heavy)",
        )
        parser.add_argument(
            "--slop",
            type=int,
            default=0,
            help="Maximum number of words that can be skipped or their order in "
            "the sentence be swapped",
        )
        parser.add_argument(
            "--size", type=int, default=10, help="Maximum number of hits to return (default: 10)"
        )

    def handle(self, *args, **options):  # NOQA
        audio_pk: int = options["audio_pk"]
        typification_pk: Optional[int] = options.get("typification_pk")
        sentence: Optional[str] = options.get("sentence")
        explain: bool = options.get("explain", False)
        size: int = options.get("size", 10)
        slop: int = options.get("slop", 0)

        if not typification_pk and not sentence:
            raise CommandError("You must provide either --typification-pk or --sentence")
        if typification_pk and sentence:
            raise CommandError("Provide only one of --typification-pk or --sentence, not both")

        # Validate audio exists
        try:
            audio = Audio.objects.get(pk=audio_pk)
        except Audio.DoesNotExist:
            raise CommandError(f"Audio with pk={audio_pk} does not exist")

        should_queries: List[Q] = []
        patterns_desc = []

        if typification_pk:
            try:
                typification = Typification.objects.prefetch_related("patterns").get(
                    pk=typification_pk
                )
            except Typification.DoesNotExist:
                raise CommandError(f"Typification with pk={typification_pk} does not exist")

            for pattern in typification.patterns.all():
                text_opts = {"query": pattern.cleaned_sentence, "_name": f"pattern_{pattern.pk}"}
                if pattern.is_variable:
                    text_opts.update({"slop": pattern.slop})
                should_queries.append(Q("match_phrase", text=text_opts))
                patterns_desc.append(
                    {
                        "pattern_pk": pattern.pk,
                        "sentence": pattern.cleaned_sentence,
                        "slop": pattern.slop if pattern.is_variable else 0,
                        "is_variable": pattern.is_variable,
                    }
                )
        else:
            # Single sentence mode
            text_opts = {"query": sentence, "_name": "input_sentence", "slop": slop}
            should_queries.append(Q("match_phrase", text=text_opts))
            patterns_desc.append(
                {"pattern_pk": None, "sentence": sentence, "slop": slop, "is_variable": False}
            )

        # Build the combined query
        query = Q(
            "bool",
            filter=[Q("term", audio_id=audio.pk)],
            should=should_queries,
            minimum_should_match=1,
        )

        search = AudioSegmentDocument.search().query(query)[:size]
        if explain:
            search = search.extra(explain=True)

        # Print the compiled search DSL
        self.stdout.write(self.style.NOTICE("=== Elasticsearch DSL (query) ==="))
        self.stdout.write(json.dumps(search.to_dict(), ensure_ascii=False, indent=2))

        # Extra context
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("=== Context ==="))
        ctx = {
            "audio_pk": audio.pk,
            "typification_pk": typification_pk,
            "patterns": patterns_desc,
            "size": size,
            "explain": explain,
            "index": AudioSegmentDocument._index._name,
        }
        self.stdout.write(json.dumps(ctx, ensure_ascii=False, indent=2))

        # Run the search and output diagnostics
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("=== Executing search... ==="))
        try:
            results = search.execute()
        except Exception as e:
            # Show a helpful error and stop
            raise CommandError(f"Error executing search: {getattr(e, 'error', str(e))}")

        total_hits = len(results.hits)
        self.stdout.write(self.style.SUCCESS(f"Got {total_hits} hit(s)."))

        if total_hits == 0:
            return

        # Print per-hit information
        for idx, hit in enumerate(results.hits):
            self.stdout.write("")
            self.stdout.write(self.style.NOTICE(f"-- Hit #{idx + 1} --"))
            meta = getattr(hit, "meta", None)
            matched = []
            score = None
            explanation = None
            if meta is not None:
                matched = list(getattr(meta, "matched_queries", []) or [])
                score = getattr(meta, "score", None)
                if explain:
                    explanation = getattr(meta, "explanation", None)

            hit_info = {
                "id": getattr(hit, "id", None),
                "audio_id": getattr(hit, "audio_id", None),
                "speaker_label": getattr(hit, "speaker_label", None),
                "text": getattr(hit, "text", None),
                "score": score,
                "matched_queries": matched,
            }
            self.stdout.write(json.dumps(hit_info, ensure_ascii=False, indent=2))

            if explain and explanation is not None:
                # Explanation is a nested structure; make it JSON-serializable
                def expl_to_dict(expl):
                    if isinstance(expl, dict):
                        return {k: expl_to_dict(v) for k, v in expl.items()}
                    if hasattr(expl, "to_dict"):
                        return expl.to_dict()
                    if isinstance(expl, (list, tuple)):
                        return [expl_to_dict(x) for x in expl]
                    return expl

                self.stdout.write(self.style.NOTICE("  Explanation:"))
                self.stdout.write(
                    json.dumps(expl_to_dict(explanation), ensure_ascii=False, indent=2)
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Done."))
