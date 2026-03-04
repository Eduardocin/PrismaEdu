"""
examples.py
Gerador de exemplos práticos com few-shot.
"""

from app.generators._base import run_generator
from app.prompts.schemas import ExamplesResponse


MAX_OUTPUT_TOKENS = 800


def generate_examples(
    profile: dict,
    topic: str,
    version: str = "v2",
    temperature: float = 0.7,
) -> ExamplesResponse | dict:
    """
    Gera um exemplo prático personalizado para o aluno.

    Retorna ExamplesResponse (v2) ou dict com chave 'raw' (v1).
    """
    return run_generator(
        profile,
        topic,
        "examples",
        version,
        temperature,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
