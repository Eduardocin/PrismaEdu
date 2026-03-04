"""
_parsers.py
Funções puras de parse JSON — sem dependências externas.
Usadas por _base.py e testáveis de forma isolada.
"""

import re


def _is_truncated(raw: str) -> bool:
    """Retorna True se o JSON parece cortado (começa com { mas não termina com } ou }"')"""
    stripped = raw.strip()
    if not stripped.startswith("{"):
        return False
    return not (stripped.endswith("}") or stripped.endswith('}"'))


def _safe_parse(raw: str, model_class):
    """
    Tenta parsear 'raw' como JSON validado pelo model_class.

    Estratégias em ordem:
      1. Detecta truncamento → {"raw": ..., "truncated": True}
      2. model_validate_json direto
      3. Fallback: extrai bloco ```json``` e tenta novamente
      4. Falha silenciosa → {"raw": ..., "truncated": False}
    """
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
