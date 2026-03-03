"""
schemas.py
Modelos Pydantic que definem o Output Schema de cada tipo de conteúdo.
O Gemini os usa para garantir respostas em JSON estruturado e validado.
"""

from pydantic import BaseModel, Field


class ConceptualResponse(BaseModel):
    """Schema para explicações conceituais com chain-of-thought."""
    definition: str = Field(description="Definição simples do conceito em 1-2 frases")
    why_it_matters: str = Field(description="Por que este conceito é importante para o aluno")
    steps: list[str] = Field(description="Explicação passo a passo (mínimo 3 itens)")
    summary: str = Field(description="Resumo final consolidando o aprendizado")


class ExamplesResponse(BaseModel):
    """Schema para exemplos práticos com few-shot."""
    context: str = Field(description="Contexto e motivação do exemplo")
    example: str = Field(description="Exemplo completo e funcional")
    explanation: list[str] = Field(description="O que cada parte do exemplo faz")
    variation: str = Field(description="Variação ou exercício proposto ao aluno")


class ReflectionResponse(BaseModel):
    """Schema para perguntas de reflexão crítica."""
    questions: list[str] = Field(
        description="Exatamente 3 perguntas de reflexão, da mais simples à mais desafiadora",
        min_length=3,
        max_length=3,
    )


class VisualResponse(BaseModel):
    """Schema para representação visual e analógica."""
    analogy: str = Field(description="Analogia do cotidiano conectada aos interesses do aluno")
    visual_representation: str = Field(
        description="Representação textual: tabela, lista hierárquica ou diagrama ASCII"
    )
    legend: str = Field(description="Legenda explicando os elementos da representação")


# ── Mapa central: content_type → schema Pydantic ─────────────────────────────

SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "conceptual": ConceptualResponse,
    "examples":   ExamplesResponse,
    "reflection": ReflectionResponse,
    "visual":     VisualResponse,
}


def get_schema(content_type: str) -> type[BaseModel]:
    """Retorna o modelo Pydantic correspondente ao content_type."""
    if content_type not in SCHEMA_MAP:
        raise ValueError(f"content_type inválido: '{content_type}'. Use: {list(SCHEMA_MAP)}")
    return SCHEMA_MAP[content_type]
