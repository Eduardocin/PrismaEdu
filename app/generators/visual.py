"""
visual.py
Gerador de explicações visuais e analógicas.
"""

from app.generators._base import run_generator
from app.prompts.schemas import VisualResponse


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
    return run_generator(profile, topic, "visual", version, temperature)


if __name__ == "__main__":
    from app.profiles.profile_manager import get_profile_by_id

    profile = get_profile_by_id("student_003")  # Larissa — auditivo/avançado
    resultado = generate_visual(profile, "recursividade")

    print(f"Aluno : {profile['nome']}")
    print(f"Tópico: recursividade\n")
    if isinstance(resultado, dict):
        print(resultado["raw"])
    else:
        print(f"Analogia           : {resultado.analogy}")
        print(f"Representação visual:\n{resultado.visual_representation}")
        print(f"Legenda            : {resultado.legend}")
