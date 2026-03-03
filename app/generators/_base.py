"""
_base.py
Função compartilhada por todos os generators.
Orquestra: cache → prompt_builder → gemini_client → validação Pydantic → cache → output.
"""

import json
from pydantic import BaseModel, ValidationError
from app.prompts.prompt_builder import build_prompt
from app.services.gemini_client import generate
from app.services import cache as cache_service
from app.storage.output_manager import save as save_output


def run_generator(
    profile: dict,
    topic: str,
    content_type: str,
    version: str = "v2",
    temperature: float = 0.7,
    use_cache: bool = True,
    save: bool = True,
) -> BaseModel:
    """
    Executa o pipeline completo de geração de conteúdo:
      1. Verifica cache (se use_cache=True)
      2. Monta o prompt (build_prompt)
      3. Chama a API Gemini (generate)
      4. Parseia e valida o JSON retornado (Pydantic)
      5. Salva no cache
      6. Persiste o output em JSON (se save=True)

    Args:
        profile: Perfil do aluno (dict do students.json).
        topic: Tema a ser ensinado.
        content_type: Tipo de conteúdo ('conceptual', 'examples', 'reflection', 'visual').
        version: Versão do prompt ('v1' ou 'v2').
        temperature: Criatividade da resposta.
        use_cache: Se True, tenta servir do cache antes de chamar a API.
        save: Se True, persiste o resultado em storage/outputs/.

    Returns:
        Instância Pydantic validada (v2) ou dict com 'raw' (v1).

    Raises:
        RuntimeError: Se a API falhar ou o JSON não puder ser validado.
    """
    student_id = profile.get("id", "unknown")

    # 1. Verificar cache
    if use_cache and version == "v2":
        cached = cache_service.get(student_id, topic, content_type, version)
        if cached:
            _, _, schema = build_prompt(profile, topic, content_type, version)
            return schema.model_validate(cached["data"])

    # 2. Montar prompt
    system, prompt, schema = build_prompt(profile, topic, content_type, version)

    # 3. Chamar API
    raw = generate(
        prompt=prompt,
        system_instruction=system,
        temperature=temperature,
        response_schema=schema,
    )

    # 4. v1: retorna texto bruto
    if schema is None:
        return {"raw": raw}

    # 5. Validar com Pydantic
    try:
        data = json.loads(raw)
        result = schema.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise RuntimeError(
            f"Falha ao validar resposta do Gemini para '{content_type}': {e}\n"
            f"Resposta bruta: {raw[:300]}"
        ) from e

    # 6. Salvar no cache
    if use_cache and version == "v2":
        cache_service.set(student_id, topic, content_type, version, data)

    # 7. Persistir output
    if save and version == "v2":
        save_output(profile, topic, content_type, version, result)

    return result
