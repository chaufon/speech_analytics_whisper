import ast
import logging

logger = logging.getLogger(__name__)


def calculate_wer(master_file: str, hypothesis_file: str) -> float:
    import jiwer

    wer = 0.0
    master = open(master_file, "r").read()
    reference = " ".join(ast.literal_eval(master))
    hypothesis = open(hypothesis_file, "r").read()
    spanish_transform = jiwer.Compose(
        [
            jiwer.ToLowerCase(),
            jiwer.Strip(),
            jiwer.RemoveMultipleSpaces(),
            jiwer.RemovePunctuation(),
            jiwer.RemoveEmptyStrings(),
        ]
    )
    reference_normalized = spanish_transform(reference)
    hypothesis_normalized = spanish_transform(hypothesis)
    logger.info(f"Reference normalized: {reference_normalized}")
    logger.info(f"Hypothesis normalized: {hypothesis_normalized}")
    try:
        wer = jiwer.wer(reference_normalized, hypothesis_normalized)
    except Exception as e:
        logger.error(f"Error al calcular WER: {e}")
    return wer
