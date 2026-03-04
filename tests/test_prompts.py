"""
test_prompts.py
Testes do Prisma — cobrindo montagem de prompts, cache e output_manager.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# ── Fixtures compartilhadas ──────────────────────────────────────────────────

@pytest.fixture
def profile_fixture():
    """Perfil sintético de aluno — sem depender do students.json."""
    return {
        "id": "student_test",
        "nome": "Aluno Teste",
        "idade": 16,
        "nivel": "intermediário",
        "estilo_aprendizado": "visual",
        "descricao": "Aprende bem com exemplos visuais e práticos.",
    }


# ════════════════════════════════════════════════════════════════════════════
# BLOCO 1 — Montagem do prompt
# ════════════════════════════════════════════════════════════════════════════

class TestPromptBuilder:
    """Verifica se build_prompt monta corretamente system e user prompt."""

    def test_v2_system_contem_persona(self, profile_fixture):
        """v2 deve incluir a persona do professor no system instruction."""
        from app.prompts.prompt_builder import build_prompt
        from app.prompts.base_prompts import SYSTEM_PERSONA

        system, _, _ = build_prompt(profile_fixture, "fotossíntese", "conceptual", "v2")

        assert system == SYSTEM_PERSONA, (
            "system instruction v2 deve ser exatamente SYSTEM_PERSONA"
        )

    def test_v2_prompt_contem_contexto_do_aluno(self, profile_fixture):
        """v2 deve incluir nome, nível e estilo do aluno no prompt."""
        from app.prompts.prompt_builder import build_prompt

        _, prompt, _ = build_prompt(profile_fixture, "fotossíntese", "conceptual", "v2")

        assert "Aluno Teste" in prompt, "Nome do aluno deve estar no prompt"
        assert "intermediário" in prompt, "Nível do aluno deve estar no prompt"
        assert "visual" in prompt, "Estilo de aprendizado deve estar no prompt"

    def test_v2_retorna_schema_pydantic(self, profile_fixture):
        """v2 deve retornar um schema Pydantic (não None)."""
        from app.prompts.prompt_builder import build_prompt
        from pydantic import BaseModel

        _, _, schema = build_prompt(profile_fixture, "fotossíntese", "conceptual", "v2")

        assert schema is not None, "Schema v2 não deve ser None"
        assert issubclass(schema, BaseModel), "Schema deve ser subclasse de BaseModel"

    def test_v1_system_vazio(self, profile_fixture):
        """v1 não usa system instruction — deve retornar string vazia."""
        from app.prompts.prompt_builder import build_prompt

        system, _, schema = build_prompt(profile_fixture, "fotossíntese", "conceptual", "v1")

        assert system == "", "system instruction v1 deve ser string vazia"
        assert schema is None, "Schema v1 deve ser None"

    def test_topico_presente_em_todos_os_tipos(self, profile_fixture):
        """O tópico informado deve aparecer no prompt de todos os content_types."""
        from app.prompts.prompt_builder import build_prompt

        topic = "recursividade_unica_xyz"
        for content_type in ["conceptual", "examples", "reflection", "visual"]:
            _, prompt, _ = build_prompt(profile_fixture, topic, content_type, "v2")
            assert topic in prompt, (
                f"Tópico '{topic}' não encontrado no prompt de '{content_type}'"
            )

    def test_content_type_invalido_levanta_erro(self, profile_fixture):
        """content_type desconhecido deve levantar ValueError."""
        from app.prompts.prompt_builder import build_prompt

        with pytest.raises(ValueError, match="content_type inválido"):
            build_prompt(profile_fixture, "fotossíntese", "invalido", "v2")

    def test_version_invalida_levanta_erro(self, profile_fixture):
        """version desconhecida deve levantar ValueError."""
        from app.prompts.prompt_builder import build_prompt

        with pytest.raises(ValueError, match="version inválida"):
            build_prompt(profile_fixture, "fotossíntese", "conceptual", "v99")


# ════════════════════════════════════════════════════════════════════════════
# BLOCO 2 — Cache (hit e miss)
# ════════════════════════════════════════════════════════════════════════════

class TestCache:
    """Testa o ciclo completo de cache: miss → set → hit → invalidate."""

    @pytest.fixture(autouse=True)
    def _cache_temp(self, tmp_path, monkeypatch):
        temp_cache = tmp_path / "cache.json"
        import app.services.cache as cache_module
        monkeypatch.setattr(cache_module, "_CACHE_FILE", temp_cache)

    def test_miss_retorna_none(self):
        """Chave inexistente deve retornar None."""
        from app.services import cache as cache_service

        resultado = cache_service.get("student_x", "fotossíntese", "conceptual", "v2")
        assert resultado is None

    def test_set_e_hit(self):
        """Após set, get deve retornar os dados salvos."""
        from app.services import cache as cache_service

        dados = {"definition": "Processo de conversão de luz em energia."}
        cache_service.set("student_x", "fotossíntese", "conceptual", "v2", dados)

        hit = cache_service.get("student_x", "fotossíntese", "conceptual", "v2")

        assert hit is not None, "Deve haver cache hit após set"
        assert hit["data"] == dados, "Dados recuperados devem ser idênticos aos salvos"

    def test_chave_diferente_e_miss(self):
        """Chaves distintas não devem colidir."""
        from app.services import cache as cache_service

        dados = {"definition": "teste"}
        cache_service.set("student_x", "fotossíntese", "conceptual", "v2", dados)

        assert cache_service.get("student_x", "OUTRO_TOPICO", "conceptual", "v2") is None
        assert cache_service.get("student_x", "fotossíntese", "conceptual", "v1") is None

    def test_invalidate_remove_entrada(self):
        """invalidate deve remover a entrada e retornar True."""
        from app.services import cache as cache_service

        cache_service.set("student_x", "fotossíntese", "conceptual", "v2", {"k": "v"})
        removido = cache_service.invalidate("student_x", "fotossíntese", "conceptual", "v2")

        assert removido is True
        assert cache_service.get("student_x", "fotossíntese", "conceptual", "v2") is None

    def test_invalidate_chave_inexistente_retorna_false(self):
        """invalidate em chave inexistente deve retornar False sem erro."""
        from app.services import cache as cache_service

        resultado = cache_service.invalidate("ghost", "nada", "conceptual", "v2")
        assert resultado is False

    def test_cache_persiste_em_disco(self, tmp_path, monkeypatch):
        """O cache deve estar gravado em JSON no disco após set."""
        import app.services.cache as cache_module
        temp_cache = tmp_path / "cache_disco.json"
        monkeypatch.setattr(cache_module, "_CACHE_FILE", temp_cache)

        cache_module.set("s1", "topico", "conceptual", "v2", {"x": 1})

        assert temp_cache.exists(), "Arquivo de cache deve ser criado no disco"
        with open(temp_cache, encoding="utf-8") as f:
            conteudo = json.load(f)
        assert len(conteudo) == 1, "Cache deve ter exatamente 1 entrada"


# ════════════════════════════════════════════════════════════════════════════
# BLOCO 3 — Output Manager
# ════════════════════════════════════════════════════════════════════════════

class TestOutputManager:
    """Verifica se save() grava JSON correto no disco."""

    @pytest.fixture(autouse=True)
    def _output_temp(self, tmp_path, monkeypatch):
        """Redireciona _OUTPUTS_DIR para diretório temporário."""
        import app.storage.output_manager as om
        monkeypatch.setattr(om, "_OUTPUTS_DIR", tmp_path / "outputs")
        monkeypatch.setattr(om, "_SAMPLES_DIR", tmp_path / "samples")
        self.tmp_path = tmp_path

    def _fake_result(self):
        """Retorna um resultado sintético sem chamar a API."""
        from app.prompts.schemas import ConceptualResponse
        return ConceptualResponse(
            definition="Fotossíntese é a conversão de luz em energia.",
            why_it_matters="Sustenta a cadeia alimentar.",
            steps=["Absorção de luz", "Conversão em glicose", "Liberação de O2"],
            summary="Processo vital para todos os seres vivos.",
        )

    def test_arquivo_json_e_criado(self, profile_fixture):
        """save() deve criar um arquivo .json no disco."""
        from app.storage.output_manager import save

        path = save(profile_fixture, "fotossíntese", "conceptual", "v2", self._fake_result())

        assert path.exists(), "Arquivo de output deve existir"
        assert path.suffix == ".json", "Arquivo deve ter extensão .json"

    def test_estrutura_do_json(self, profile_fixture):
        """JSON salvo deve conter 'metadata' e 'result' com campos corretos."""
        from app.storage.output_manager import save

        path = save(profile_fixture, "fotossíntese", "conceptual", "v2", self._fake_result())

        with open(path, encoding="utf-8") as f:
            payload = json.load(f)

        assert "metadata" in payload, "JSON deve ter chave 'metadata'"
        assert "result" in payload, "JSON deve ter chave 'result'"

        meta = payload["metadata"]
        assert meta["student_id"] == "student_test"
        assert meta["topic"] == "fotossíntese"
        assert meta["content_type"] == "conceptual"
        assert meta["prompt_version"] == "v2"

    def test_result_contem_campos_do_schema(self, profile_fixture):
        """'result' deve conter os campos do ConceptualResponse."""
        from app.storage.output_manager import save

        path = save(profile_fixture, "fotossíntese", "conceptual", "v2", self._fake_result())

        with open(path, encoding="utf-8") as f:
            payload = json.load(f)

        result = payload["result"]
        assert "definition" in result
        assert "why_it_matters" in result
        assert "steps" in result
        assert isinstance(result["steps"], list)
        assert "summary" in result

    def test_diretorio_e_criado_automaticamente(self, profile_fixture):
        """save() deve criar a hierarquia de diretórios automaticamente."""
        from app.storage.output_manager import save

        path = save(profile_fixture, "fotossíntese", "reflection", "v2",
                    {"raw": "resposta bruta de reflexão"})

        assert path.parent.exists(), "Diretório de output deve ser criado"

    def test_salvar_em_samples(self, profile_fixture):
        """dest='samples' deve salvar no diretório samples."""
        from app.storage.output_manager import save

        path = save(
            profile_fixture, "fotossíntese", "conceptual", "v2",
            self._fake_result(), dest="samples"
        )

        assert "samples" in str(path), "Path deve estar dentro do diretório samples"
        assert path.exists()
