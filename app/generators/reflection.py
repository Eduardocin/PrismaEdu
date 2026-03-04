"""
reflection.py
Gerador de perguntas de reflexão crítica.
"""

from app.generators._base import run_generator
from app.prompts.schemas import ReflectionResponse


MAX_OUTPUT_TOKENS = 600


def generate_reflection(
    profile: dict,
    topic: str,
    version: str = "v2",
    temperature: float = 0.8,
) -> ReflectionResponse | dict:
    """
    Gera perguntas de reflexão crítica personalizadas para o aluno.

    Retorna ReflectionResponse (v2) ou dict com chave 'raw' (v1).
    """
    return run_generator(
        profile,
        topic,
        "reflection",
        version,
        temperature,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
