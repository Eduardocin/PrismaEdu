"""
_base.py
Função compartilhada por todos os generators.
Orquestra: cache → prompt_builder → gemini_client → validação Pydantic → cache → output.
"""

import re
from pydantic import BaseModel
from app.prompts.prompt_builder import build_prompt
from app.services.gemini_client import generate
from app.services import cache as cache_service
from app.storage.output_manager import save as save_output


def _is_truncated(raw: str) -> bool:
    stripped = raw.strip()
    return not (stripped.endswith("}") or stripped.endswith('}"'))


def _safe_parse(raw: str, model_class):
    if _is_truncated(raw):
        return {"raw": raw, "truncated": True}
    try:
        return model_class.model_validate_json(raw)
    except Exception:
        pass
    match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
    if match:
        try:
            return model_class.model_validate_json(match.group(1))
        except Exception:
            pass
    return {"raw": raw, "truncated": False}


def run_generator(
    profile: dict,
    topic: str,
    content_type: str,
    version: str = "v2",
    temperature: float = 0.7,
    use_cache: bool = True,
    save: bool = True,
    max_output_tokens: int | None = None,
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
        profile: Dicionário com os dados do aluno (nome, idade, nivel, estilo_aprendizado, etc.).
        topic: Tema a ser ensinado.
        content_type: Tipo de conteúdo ('conceptual', 'examples', 'reflection', 'visual').
        version: Versão do prompt ('v1' ou 'v2').
        temperature: Criatividade da resposta.
        use_cache: Se True, tenta servir do cache antes de chamar a API.
        save: Se True, persiste o resultado em storage/outputs/.
        max_output_tokens: Limite de tokens no output. None = sem limite explícito.

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
        max_output_tokens=max_output_tokens,
    )

    # 4. v1: retorna texto bruto
    if schema is None:
        return {"raw": raw}

    # 5. Parsear e validar com Pydantic (com detecção de truncamento)
    result = _safe_parse(raw, schema)

    # Se retornou dict (truncado ou parse falhou), não persiste
    if isinstance(result, dict):
        return result

    # 6. Salvar no cache
    if use_cache and version == "v2":
        cache_service.set(student_id, topic, content_type, version, result.model_dump())

    # 7. Persistir output
    if save and version == "v2":
        save_output(profile, topic, content_type, version, result)

    return result
