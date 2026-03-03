"""
cache.py
Cache simples baseado em arquivo JSON.
Chave: hash SHA-256 de (student_id + topic + content_type + prompt_version).
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

_CACHE_FILE = Path(__file__).parent.parent / "storage" / "cache.json"


def _make_key(student_id: str, topic: str, content_type: str, version: str) -> str:
    """Gera um hash SHA-256 a partir dos 4 parâmetros de identificação."""
    raw = f"{student_id}|{topic.strip().lower()}|{content_type}|{version}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _load() -> dict:
    """Carrega o arquivo de cache. Retorna dict vazio se não existir."""
    if not _CACHE_FILE.exists():
        return {}
    with open(_CACHE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    """Persiste o dicionário de cache no arquivo JSON."""
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get(student_id: str, topic: str, content_type: str, version: str) -> dict | None:
    """
    Busca uma entrada no cache.

    Returns:
        Dict com os dados salvos, ou None se não houver cache.
    """
    key = _make_key(student_id, topic, content_type, version)
    return _load().get(key)


def set(student_id: str, topic: str, content_type: str, version: str, data: dict) -> None:
    """
    Salva uma entrada no cache.

    Args:
        data: Dict com o conteúdo gerado (já serializado — sem objetos Pydantic).
    """
    key = _make_key(student_id, topic, content_type, version)
    cache = _load()
    cache[key] = {
        "student_id": student_id,
        "topic": topic,
        "content_type": content_type,
        "version": version,
        "cached_at": datetime.utcnow().isoformat(),
        "data": data,
    }
    _save(cache)


def invalidate(student_id: str, topic: str, content_type: str, version: str) -> bool:
    """
    Remove uma entrada específica do cache.

    Returns:
        True se existia e foi removida, False se não existia.
    """
    key = _make_key(student_id, topic, content_type, version)
    cache = _load()
    if key in cache:
        del cache[key]
        _save(cache)
        return True
    return False


def clear() -> int:
    """Remove todas as entradas do cache. Retorna o número de entradas removidas."""
    cache = _load()
    count = len(cache)
    _save({})
    return count


def stats() -> dict:
    """Retorna estatísticas do cache atual."""
    cache = _load()
    return {
        "total_entries": len(cache),
        "cache_file": str(_CACHE_FILE),
        "entries": [
            {
                "student_id": v["student_id"],
                "topic": v["topic"],
                "content_type": v["content_type"],
                "version": v["version"],
                "cached_at": v["cached_at"],
            }
            for v in cache.values()
        ],
    }


if __name__ == "__main__":
    print("=== Teste do cache ===\n")

    # Salvar entradas
    set("student_001", "funções em Python", "conceptual", "v2", {"definition": "teste"})
    set("student_002", "listas", "examples", "v2", {"example": "lista = [1,2,3]"})

    # Buscar hit
    resultado = get("student_001", "funções em Python", "conceptual", "v2")
    print(f"HIT  : {resultado['data']}")

    # Buscar miss
    resultado = get("student_999", "tópico inexistente", "conceptual", "v2")
    print(f"MISS : {resultado}")

    # Estatísticas
    s = stats()
    print(f"\nEntradas no cache: {s['total_entries']}")
    for e in s["entries"]:
        print(f"  [{e['content_type']}/{e['version']}] {e['student_id']} — '{e['topic']}'")

    # Invalidar uma entrada
    removida = invalidate("student_001", "funções em Python", "conceptual", "v2")
    print(f"\nInvalidado: {removida}")
    print(f"Entradas restantes: {stats()['total_entries']}")

    # Limpar tudo
    total = clear()
    print(f"Cache limpo: {total} entra(s) removida(s)")
