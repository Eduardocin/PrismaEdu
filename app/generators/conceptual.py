"""
conceptual.py
Gerador de explicações conceituais com chain-of-thought.
"""

from app.generators._base import run_generator
from app.prompts.schemas import ConceptualResponse


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
    return run_generator(profile, topic, "conceptual", version, temperature)


if __name__ == "__main__":
    import json
    from app.profiles.profile_manager import get_profile_by_id

    profile = get_profile_by_id("student_001")  # Ana Beatriz — visual/iniciante
    resultado = generate_conceptual(profile, "funções em Python")

    print(f"Aluno : {profile['nome']}")
    print(f"Tópico: funções em Python\n")
    if isinstance(resultado, dict):
        print(resultado["raw"])
    else:
        print(f"Definição    : {resultado.definition}")
        print(f"Importância  : {resultado.why_it_matters}")
        print(f"Passos      :")
        for i, step in enumerate(resultado.steps, 1):
            print(f"  {i}. {step}")
        print(f"Resumo      : {resultado.summary}")
