"""
test_integration.py
Testes de integração — valida correções da branch fix/token-limit-and-visual:
  - _safe_parse com JSON truncado retorna {"truncated": True}
  - _safe_parse com JSON válido retorna instância Pydantic
  - _safe_parse com JSON em bloco ```json``` faz o fallback
  - _format_result exibe alerta quando truncated=True
  - _format_result não exibe alerta quando truncated=False
  - Prompts visuais contêm as restrições de tamanho e estilo ASCII
  - max_output_tokens por generator estão nos valores corretos
"""

import pytest


# ════════════════════════════════════════════════════════════════════════════
# BLOCO 1 — _safe_parse (app/generators/_base.py)
# ════════════════════════════════════════════════════════════════════════════


class TestSafeParse:
    """Valida o parser JSON robusto centralizado em _base.py."""

    @pytest.fixture
    def conceptual_schema(self):
        from app.prompts.schemas import ConceptualResponse

        return ConceptualResponse

    def test_json_truncado_retorna_truncated_true(self, conceptual_schema):
        """JSON sem fechar } deve retornar dict com truncated=True."""
        from app.generators._parsers import _safe_parse

        raw = '{"definition": "Fotossíntese", "why_it_matters": "Vital"'
        result = _safe_parse(raw, conceptual_schema)

        assert isinstance(result, dict), "Deve retornar dict"
        assert result["truncated"] is True
        assert result["raw"] == raw

    def test_json_valido_retorna_pydantic(self, conceptual_schema):
        """JSON completo e válido deve retornar instância Pydantic."""
        from app.generators._parsers import _safe_parse

        raw = """{
            "definition": "Processo de converter luz em energia.",
            "why_it_matters": "Base da cadeia alimentar.",
            "steps": ["Absorção de luz", "Produção de glicose", "Liberação de O2"],
            "summary": "Essencial para a vida."
        }"""
        result = _safe_parse(raw, conceptual_schema)

        assert not isinstance(result, dict), (
            "Deve retornar instância Pydantic, não dict"
        )
        assert result.definition == "Processo de converter luz em energia."

    def test_json_em_bloco_markdown_e_parseado(self, conceptual_schema):
        """JSON dentro de ```json``` deve ser extraído e parseado via fallback."""
        from app.generators._parsers import _safe_parse

        raw = """Aqui está a resposta:
```json
{
    "definition": "Definição via fallback.",
    "why_it_matters": "Importa.",
    "steps": ["Passo 1"],
    "summary": "Resumo."
}
```"""
        result = _safe_parse(raw, conceptual_schema)

        assert not isinstance(result, dict), "Fallback deve retornar instância Pydantic"
        assert result.definition == "Definição via fallback."

    def test_json_invalido_sem_truncamento_retorna_truncated_false(
        self, conceptual_schema
    ):
        """Texto que não é JSON e não é truncado deve retornar truncated=False."""
        from app.generators._parsers import _safe_parse

        raw = "Resposta em texto puro sem JSON."
        result = _safe_parse(raw, conceptual_schema)

        assert isinstance(result, dict)
        assert result["truncated"] is False
        assert result["raw"] == raw

    def test_is_truncated_json_bem_formado(self):
        """_is_truncated deve retornar False para JSON fechado."""
        from app.generators._parsers import _is_truncated

        assert _is_truncated('{"a": "b"}') is False
        assert _is_truncated('{"a": "b"}"') is False

    def test_is_truncated_json_aberto(self):
        """_is_truncated deve retornar True para JSON sem fechar."""
        from app.generators._parsers import _is_truncated

        assert _is_truncated('{"definition": "texto sem fechar') is True
        assert _is_truncated("") is False  # string vazia não é JSON truncado
        assert _is_truncated("Texto qualquer") is False  # texto puro não é JSON


# ════════════════════════════════════════════════════════════════════════════
# BLOCO 2 — _format_result (app/interface.py)
# ════════════════════════════════════════════════════════════════════════════


class TestFormatResult:
    """Valida o alerta de truncamento na interface."""

    def test_truncado_exibe_alerta(self):
        """result com truncated=True deve exibir o bloco de aviso."""
        from app.interface import _format_result

        result = {"raw": "conteúdo parcial...", "truncated": True}
        output = _format_result(result)

        assert "⚠️" in output, "Alerta de truncamento deve estar presente"
        assert "Resposta incompleta" in output
        assert "conteúdo parcial..." in output

    def test_nao_truncado_sem_alerta(self):
        """result com truncated=False não deve exibir o bloco de aviso."""
        from app.interface import _format_result

        result = {"raw": "resposta completa", "truncated": False}
        output = _format_result(result)

        assert "⚠️" not in output, "Não deve exibir alerta quando não truncado"
        assert "resposta completa" in output

    def test_raw_sem_truncated_sem_alerta(self):
        """result sem chave 'truncated' (compatibilidade) não deve exibir alerta."""
        from app.interface import _format_result

        result = {"raw": "resposta v1"}
        output = _format_result(result)

        assert "⚠️" not in output
        assert "resposta v1" in output


# ════════════════════════════════════════════════════════════════════════════
# BLOCO 3 — Restrições nos prompts visuais
# ════════════════════════════════════════════════════════════════════════════


class TestVisualPromptConstraints:
    """Valida que os prompts visuais contêm as restrições de tamanho/estilo."""

    def test_visual_v1_contem_restricoes_ascii(self):
        from app.prompts.prompt_versions import VISUAL_V1

        assert "8 linhas" in VISUAL_V1
        assert "60 caracteres" in VISUAL_V1
        assert "-->" in VISUAL_V1
        assert "bordas duplas" in VISUAL_V1
        assert "visual_representation" in VISUAL_V1

    def test_visual_v2_contem_restricoes_ascii(self):
        from app.prompts.prompt_versions import VISUAL_V2

        assert "8 linhas" in VISUAL_V2
        assert "60 caracteres" in VISUAL_V2
        assert "-->" in VISUAL_V2
        assert "bordas duplas" in VISUAL_V2
        assert "visual_representation" in VISUAL_V2

    def test_visual_v2_contem_restricao_analogia(self):
        from app.prompts.prompt_versions import VISUAL_V2

        assert "3 frases curtas" in VISUAL_V2
        assert (
            "estilo_aprendizado" in VISUAL_V2
            or "estilo {estilo_aprendizado}" in VISUAL_V2
        )

    def test_todos_prompts_contem_restricao_conciseness(self):
        from app.prompts.prompt_versions import (
            CONCEPTUAL_V1,
            CONCEPTUAL_V2,
            EXAMPLES_V1,
            EXAMPLES_V2,
            REFLECTION_V1,
            REFLECTION_V2,
            VISUAL_V1,
            VISUAL_V2,
        )

        frase = "JSON de resposta deve estar sempre completo e fechado"
        for nome, prompt in [
            ("CONCEPTUAL_V1", CONCEPTUAL_V1),
            ("CONCEPTUAL_V2", CONCEPTUAL_V2),
            ("EXAMPLES_V1", EXAMPLES_V1),
            ("EXAMPLES_V2", EXAMPLES_V2),
            ("REFLECTION_V1", REFLECTION_V1),
            ("REFLECTION_V2", REFLECTION_V2),
            ("VISUAL_V1", VISUAL_V1),
            ("VISUAL_V2", VISUAL_V2),
        ]:
            assert frase in prompt, f"Restrição de conciseness ausente em {nome}"


# ════════════════════════════════════════════════════════════════════════════
# BLOCO 4 — max_output_tokens por generator
# ════════════════════════════════════════════════════════════════════════════


class TestMaxOutputTokens:
    """Valida que cada generator usa o limite de tokens correto."""

    def test_conceptual_max_tokens(self):
        from app.generators.conceptual import MAX_OUTPUT_TOKENS

        assert MAX_OUTPUT_TOKENS == 1000

    def test_examples_max_tokens(self):
        from app.generators.examples import MAX_OUTPUT_TOKENS

        assert MAX_OUTPUT_TOKENS == 1200

    def test_reflection_max_tokens(self):
        from app.generators.reflection import MAX_OUTPUT_TOKENS

        assert MAX_OUTPUT_TOKENS == 600

    def test_visual_max_tokens(self):
        from app.generators.visual import MAX_OUTPUT_TOKENS

        assert MAX_OUTPUT_TOKENS == 1200
