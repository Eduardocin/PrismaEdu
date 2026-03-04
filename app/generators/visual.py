"""
visual.py
Gerador de explicações visuais e analógicas.
"""

from app.generators._base import run_generator
from app.prompts.schemas import VisualResponse

MAX_OUTPUT_TOKENS = 1200


def generate_visual(
    profile: dict,
    topic: str,
    version: str = "v2",
    temperature: float = 0.7,
) -> VisualResponse | dict:
    """
    Gera uma explicação visual e analógica personalizada para o aluno.

    Retorna VisualResponse (v2) ou dict com chave 'raw' (v1).
    """
    return run_generator(
        profile,
        topic,
        "visual",
        version,
        temperature,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
