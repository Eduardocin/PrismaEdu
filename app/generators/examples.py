"""
examples.py
Gerador de exemplos práticos com few-shot.
"""

from app.generators._base import run_generator
from app.prompts.schemas import ExamplesResponse


MAX_OUTPUT_TOKENS = 400


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
        profile, topic, "examples", version, temperature,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )


if __name__ == "__main__":
    from app.profiles.profile_manager import get_profile_by_id

    profile = get_profile_by_id("student_004")  # Pedro — cinestésico/iniciante
    resultado = generate_examples(profile, "listas em Python")

    print(f"Aluno : {profile['nome']}")
    print(f"Tópico: listas em Python\n")
    if isinstance(resultado, dict):
        print(resultado["raw"])
    else:
        print(f"Contexto    : {resultado.context}")
        print(f"Exemplo     :\n{resultado.example}")
        print(f"Explicação  :")
        for item in resultado.explanation:
            print(f"  - {item}")
        print(f"Variação    : {resultado.variation}")
