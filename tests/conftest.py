"""
conftest.py
Configuração compartilhada de testes — mocks de dependências externas.

Garante que os testes que não chamam a API real possam importar
os generators e o gemini_client sem precisar das credenciais ou
do pacote google-generativeai instalado.
"""

import sys
import types
import os
import pytest


def _build_google_genai_mock():
    """Cria stubs mínimos para google.genai e google.genai.types."""
    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    types_mod = types.ModuleType("google.genai.types")

    class _FakeConfig:
        def __init__(self, **kwargs):
            pass

    types_mod.GenerateContentConfig = _FakeConfig

    class _FakeClient:
        def __init__(self, **kwargs):
            pass

    genai_mod.Client = _FakeClient
    genai_mod.types = types_mod

    google_mod.genai = genai_mod

    return google_mod, genai_mod, types_mod


@pytest.fixture(autouse=True)
def mock_google_genai(monkeypatch):
    """
    Injeta stubs de google.genai no sys.modules antes de cada teste.
    Também define GEMINI_API_KEY para evitar o EnvironmentError do gemini_client.
    Só atua quando o pacote real não está disponível.
    """
    try:
        from google import genai  # noqa: F401
        # Pacote real disponível — não precisa de mock
        if not os.getenv("GEMINI_API_KEY"):
            monkeypatch.setenv("GEMINI_API_KEY", "test-key-mock")
        return
    except ImportError:
        pass

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-mock")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-mock")

    # Garante que app.interface seja reimportado com os mocks ativos
    for _mod in list(sys.modules):
        if _mod in ("app.interface",) or _mod.startswith("gradio"):
            monkeypatch.delitem(sys.modules, _mod, raising=False)

    # Mock gradio se não estiver instalado
    try:
        import gradio  # noqa: F401
    except ImportError:
        gradio_mock = types.ModuleType("gradio")
        for _attr in ("Blocks", "Row", "Column", "Tabs", "TabItem",
                      "Textbox", "Number", "Dropdown", "Button",
                      "Markdown", "HTML"):
            setattr(gradio_mock, _attr, type(_attr, (), {"__init__": lambda s, *a, **k: None}))
        monkeypatch.setitem(sys.modules, "gradio", gradio_mock)
        monkeypatch.setitem(sys.modules, "gradio.components", types.ModuleType("gradio.components"))

    google_mod, genai_mod, types_mod = _build_google_genai_mock()

    monkeypatch.setitem(sys.modules, "google", google_mod)
    monkeypatch.setitem(sys.modules, "google.genai", genai_mod)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_mod)

    # Recarrega o gemini_client para pegar os stubs recém-injetados
    if "app.services.gemini_client" in sys.modules:
        monkeypatch.delitem(sys.modules, "app.services.gemini_client")
    if "app.generators._base" in sys.modules:
        monkeypatch.delitem(sys.modules, "app.generators._base")
    for key in list(sys.modules):
        if key.startswith("app.generators.") and key != "app.generators._parsers":
            monkeypatch.delitem(sys.modules, key, raising=False)
