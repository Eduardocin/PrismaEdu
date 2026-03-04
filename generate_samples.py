"""
generate_samples.py
Script temporário para gerar os 4 samples de comparação v1 vs v2.
Executa: python generate_samples.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Garante que o pacote app seja encontrado
sys.path.insert(0, str(Path(__file__).parent))

from app.generators.conceptual import generate_conceptual
from app.generators.visual import generate_visual
from app.prompts.prompt_builder import build_prompt

PROFILE = {
    "id": "user_eduardo",
    "nome": "Eduardo",
    "idade": 20,
    "nivel": "intermediario",
    "estilo_aprendizado": "visual",
    "descricao": "",
    "centro": "",
}
TOPIC = "fotossintese"
SAMPLES_DIR = Path("samples")
SAMPLES_DIR.mkdir(exist_ok=True)


def _result_to_dict(result) -> dict:
    if isinstance(result, dict):
        return result
    try:
        return result.model_dump()
    except Exception:
        return {"raw": str(result)}


def _prompt_used(profile, topic, content_type, version) -> str:
    _, prompt, _ = build_prompt(profile, topic, content_type, version)
    return prompt


def save_sample(filename: str, content_type: str, version: str, result):
    path = SAMPLES_DIR / filename
    payload = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "student": {
                "nome": PROFILE["nome"],
                "idade": PROFILE["idade"],
                "nivel": PROFILE["nivel"],
                "estilo_aprendizado": PROFILE["estilo_aprendizado"],
            },
            "topic": TOPIC,
            "content_type": content_type,
            "prompt_version": version,
        },
        "prompt_used": _prompt_used(PROFILE, TOPIC, content_type, version),
        "result": _result_to_dict(result),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ {path}")


def main():
    print("Gerando samples — Eduardo / fotossíntese\n")

    print("1/4 conceptual v1...")
    r = generate_conceptual(profile=PROFILE, topic=TOPIC, version="v1", temperature=0.5)
    save_sample("conceptual_v1.json", "conceptual", "v1", r)

    print("2/4 conceptual v2...")
    r = generate_conceptual(profile=PROFILE, topic=TOPIC, version="v2", temperature=0.5)
    save_sample("conceptual_v2.json", "conceptual", "v2", r)

    print("3/4 visual v1...")
    r = generate_visual(profile=PROFILE, topic=TOPIC, version="v1", temperature=0.7)
    save_sample("visual_v1.json", "visual", "v1", r)

    print("4/4 visual v2...")
    r = generate_visual(profile=PROFILE, topic=TOPIC, version="v2", temperature=0.7)
    save_sample("visual_v2.json", "visual", "v2", r)

    print("\nPronto! 4 samples gerados em samples/")


if __name__ == "__main__":
    main()
