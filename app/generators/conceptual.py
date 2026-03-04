"""
conceptual.py
Gerador de explicações conceituais com chain-of-thought.
"""

from app.generators._base import run_generator
from app.prompts.schemas import ConceptualResponse


MAX_OUTPUT_TOKENS = 600


def generate_conceptual(
    profile: dict,
    topic: str,
    version: str = "v2",
    temperature: float = 0.5,
) -> ConceptualResponse | dict:
    """
    Gera uma explicação conceitual personalizada para o aluno.

    Retorna ConceptualResponse (v2) ou dict com chave 'raw' (v1).
    """
    return run_generator(
        profile,
        topic,
        "conceptual",
        version,
        temperature,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
