"""
reflection.py
Gerador de perguntas de reflexão crítica.
"""

from app.generators._base import run_generator
from app.prompts.schemas import ReflectionResponse


MAX_OUTPUT_TOKENS = 300


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
        profile, topic, "reflection", version, temperature,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )


if __name__ == "__main__":
    from app.profiles.profile_manager import get_profile_by_id

    profile = get_profile_by_id("student_002")  # Carlos Eduardo — leitura-escrita/intermediário
    resultado = generate_reflection(profile, "estruturas de repetição")

    print(f"Aluno : {profile['nome']}")
    print(f"Tópico: estruturas de repetição\n")
    if isinstance(resultado, dict):
        print(resultado["raw"])
    else:
        print("Perguntas de reflexão:")
        for i, q in enumerate(resultado.questions, 1):
            print(f"  {i}. {q}")
