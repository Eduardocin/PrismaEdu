"""
profile_manager.py
Carrega e busca perfis de alunos a partir do students.json.
"""

import json
from pathlib import Path

_STUDENTS_FILE = Path(__file__).parent / "students.json"


def load_profiles() -> list[dict]:
    """Retorna a lista completa de perfis de alunos."""
    with open(_STUDENTS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["students"]


def get_profile_by_id(student_id: str) -> dict | None:
    """Busca um perfil pelo ID. Retorna None se não encontrado."""
    for student in load_profiles():
        if student["id"] == student_id:
            return student
    return None


def get_profile_by_name(nome: str) -> dict | None:
    """Busca um perfil pelo nome (case-insensitive). Retorna None se não encontrado."""
    for student in load_profiles():
        if student["nome"].lower() == nome.lower():
            return student
    return None


def list_all_names() -> list[str]:
    """Retorna uma lista com os nomes de todos os alunos."""
    return [s["nome"] for s in load_profiles()]


if __name__ == "__main__":
    print("=== Todos os alunos ===")
    for name in list_all_names():
        print(f"  - {name}")

    print("\n=== Busca por ID: student_002 ===")
    profile = get_profile_by_id("student_002")
    print(f"  {profile}")

    print("\n=== Busca por nome: Larissa Mendes ===")
    profile = get_profile_by_name("Larissa Mendes")
    print(f"  Nome   : {profile['nome']}")
    print(f"  Nível  : {profile['nivel']}")
    print(f"  Estilo : {profile['estilo_aprendizado']}")

    print("\n=== Busca inexistente ===")
    profile = get_profile_by_id("student_999")
    print(f"  Resultado: {profile}")
