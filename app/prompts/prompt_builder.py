"""
prompt_builder.py
Motor de montagem dinâmica de prompts.
Combina perfil do aluno, tipo de conteúdo e versão do prompt.
"""

from app.prompts.base_prompts import (
    SYSTEM_PERSONA,
    FORMAT_CONCEPTUAL,
    FORMAT_EXAMPLES,
    FORMAT_REFLECTION,
    FORMAT_VISUAL,
    STYLE_HINTS,
)
from app.prompts.prompt_versions import VERSIONS
from app.prompts.schemas import get_schema, SCHEMA_MAP

_FORMAT_MAP = {
    "conceptual": FORMAT_CONCEPTUAL,
    "examples":   FORMAT_EXAMPLES,
    "reflection": FORMAT_REFLECTION,
    "visual":     FORMAT_VISUAL,
}

VALID_CONTENT_TYPES = list(VERSIONS.keys())
VALID_VERSIONS = ["v1", "v2"]


def build_prompt(
    profile: dict,
    topic: str,
    content_type: str,
    version: str = "v2",
) -> tuple[str, str, type | None]:
    """
    Monta o system_instruction, o prompt do usuário e o Output Schema.

    Args:
        profile: Dicionário do perfil do aluno.
        topic: Tema a ser ensinado.
        content_type: Tipo de conteúdo ('conceptual', 'examples', 'reflection', 'visual').
        version: Versão do prompt ('v1' ou 'v2').

    Returns:
        Tupla (system_instruction, user_prompt, response_schema).
        - system_instruction: string com persona do professor (v2) ou vazia (v1).
        - user_prompt: prompt montado com contexto do aluno.
        - response_schema: modelo Pydantic para JSON estruturado (v2) ou None (v1).

    Raises:
        ValueError: Se content_type ou version forem inválidos.
    """
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(f"content_type inválido: '{content_type}'. Use: {VALID_CONTENT_TYPES}")
    if version not in VALID_VERSIONS:
        raise ValueError(f"version inválida: '{version}'. Use: {VALID_VERSIONS}")

    template = VERSIONS[content_type][version]

    interesses_str = ", ".join(profile.get("interesses", []))
    style_hint = STYLE_HINTS.get(profile.get("estilo_aprendizado", ""), "")
    format_instruction = _FORMAT_MAP[content_type]

    user_prompt = template.format(
        topic=topic,
        nome=profile.get("nome", ""),
        idade=profile.get("idade", ""),
        nivel=profile.get("nivel", ""),
        estilo_aprendizado=profile.get("estilo_aprendizado", ""),
        interesses=interesses_str,
        descricao=profile.get("descricao", ""),
        style_hint=style_hint,
        format_instruction=format_instruction,
    )

    if version == "v2":
        system = SYSTEM_PERSONA
        schema = get_schema(content_type)
    else:
        system = ""
        schema = None

    return system, user_prompt, schema


if __name__ == "__main__":
    from app.profiles.profile_manager import get_profile_by_id

    profile = get_profile_by_id("student_004")  # Pedro — cinestésico/iniciante
    topic = "variáveis em Python"

    for version in ["v1", "v2"]:
        print(f"\n{'='*60}")
        print(f"  TIPO: conceptual | VERSÃO: {version}")
        print(f"{'='*60}")
        system, prompt, schema = build_prompt(profile, topic, "conceptual", version)
        if system:
            print(f"[SYSTEM]\n{system}\n")
        print(f"[PROMPT]\n{prompt}")
        if schema:
            print(f"\n[OUTPUT SCHEMA]\n{schema.model_json_schema()}")
