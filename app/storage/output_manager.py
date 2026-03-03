"""
output_manager.py
Salva cada geração em JSON com timestamp, versão do prompt e metadados do aluno.
Estrutura de saída: outputs/{student_id}/{content_type}/{YYYYMMDD_HHMMSS}.json
"""

import json
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

_OUTPUTS_DIR = Path(__file__).parent / "outputs"
_SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"


def _serialize(data) -> dict:
    """Converte Pydantic model ou dict para dict serializável."""
    if isinstance(data, BaseModel):
        return data.model_dump()
    return data


def save(
    profile: dict,
    topic: str,
    content_type: str,
    version: str,
    result,
    dest: str = "outputs",
) -> Path:
    """
    Persiste o resultado de uma geração em JSON.

    Args:
        profile: Perfil do aluno.
        topic: Tema gerado.
        content_type: Tipo de conteúdo ('conceptual', 'examples', 'reflection', 'visual').
        version: Versão do prompt ('v1' ou 'v2').
        result: Instância Pydantic ou dict a ser salvo.
        dest: 'outputs' para outputs/   |  'samples' para samples/

    Returns:
        Path do arquivo salvo.
    """
    base_dir = _OUTPUTS_DIR if dest == "outputs" else _SAMPLES_DIR
    student_id = profile.get("id", "unknown")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    output_dir = base_dir / student_id / content_type
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"{timestamp}.json"

    payload = {
        "metadata": {
            "student_id": student_id,
            "student_name": profile.get("nome", ""),
            "student_age": profile.get("idade"),
            "student_level": profile.get("nivel", ""),
            "learning_style": profile.get("estilo_aprendizado", ""),
            "topic": topic,
            "content_type": content_type,
            "prompt_version": version,
            "generated_at": datetime.utcnow().isoformat(),
        },
        "result": _serialize(result),
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return file_path


def list_outputs(student_id: str = None, content_type: str = None) -> list[Path]:
    """
    Lista arquivos de output salvos, com filtros opcionais.

    Args:
        student_id: Filtrar por aluno (opcional).
        content_type: Filtrar por tipo de conteúdo (opcional).

    Returns:
        Lista de Paths ordenada do mais recente para o mais antigo.
    """
    if not _OUTPUTS_DIR.exists():
        return []

    pattern = (
        f"{student_id}/{content_type}/*.json" if student_id and content_type
        else f"{student_id}/**/*.json" if student_id
        else f"**/{content_type}/*.json" if content_type
        else "**/*.json"
    )

    files = sorted(_OUTPUTS_DIR.glob(pattern), reverse=True)
    return files


def load(file_path: Path) -> dict:
    """Carrega e retorna o conteúdo de um arquivo de output."""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    from app.profiles.profile_manager import get_profile_by_id
    from app.generators.conceptual import generate_conceptual
    from app.generators.examples import generate_examples

    # Gerar conteúdo real
    profile = get_profile_by_id("student_003")  # Larissa — auditivo/avançado
    topic = "decoradores em Python"

    print(f"Gerando conteúdo para {profile['nome']}...\n")

    result_conceptual = generate_conceptual(profile, topic)
    result_examples = generate_examples(profile, topic)

    # Salvar em outputs/
    path1 = save(profile, topic, "conceptual", "v2", result_conceptual)
    path2 = save(profile, topic, "examples", "v2", result_examples)
    print(f"Salvo: {path1.relative_to(Path.cwd())}")
    print(f"Salvo: {path2.relative_to(Path.cwd())}")

    # Salvar exemplo em samples/
    path_sample = save(profile, topic, "conceptual", "v2", result_conceptual, dest="samples")
    print(f"Sample: {path_sample.relative_to(Path.cwd())}")

    # Listar outputs do aluno
    print(f"\nOutputs de {profile['id']}:")
    for f in list_outputs(student_id=profile["id"]):
        print(f"  {f.relative_to(_OUTPUTS_DIR)}")

    # Carregar e inspecionar um output
    data = load(path1)
    print(f"\nMetadados do output:")
    for k, v in data["metadata"].items():
        print(f"  {k}: {v}")
