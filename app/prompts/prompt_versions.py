"""
prompt_versions.py
Define v1 (simples) e v2 (completo com todas as técnicas) para cada tipo de conteúdo.

Técnicas aplicadas na v2:
  - Persona prompting    → definida no system_instruction (base_prompts.SYSTEM_PERSONA)
  - Context setting      → perfil do aluno injetado no prompt
  - Chain-of-thought     → instrução de raciocínio passo a passo (conceptual)
  - Output formatting    → estrutura esperada da resposta (validada pelo Pydantic)
  - Few-shot             → exemplo concreto (examples)
  - Inline restrictions  → restrições simples embutidas no final de cada template v2
"""

# ─────────────────────────────────────────────────────────────────────────────
# CONCEPTUAL
# ─────────────────────────────────────────────────────────────────────────────

CONCEPTUAL_V1 = """\
Aluno: {nome} | Nível: {nivel}

Explique o conceito de '{topic}' de forma clara e direta.\
"""

CONCEPTUAL_V2 = """\
Aluno: {nome}, {idade} anos | Nível: {nivel} | Estilo: {estilo_aprendizado}
Dica de adaptação: {style_hint}

Explique o conceito de '{topic}' para este aluno.

Antes de responder, pense em voz alta: o que o aluno já deve saber? \
Quais obstáculos ele pode ter? Como tornar isso concreto para ele?

{format_instruction}
Adapte a linguagem ao nível {nivel} e ao estilo {estilo_aprendizado}.
Restrição: responda apenas sobre '{topic}', em português do Brasil, sem inventar fatos.\
"""

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLES
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLES_V1 = """\
Aluno: {nome} | Nível: {nivel}

Dê um exemplo prático de '{topic}'.\
"""

EXAMPLES_V2 = """\
Aluno: {nome}, {idade} anos | Nível: {nivel} | Estilo: {estilo_aprendizado}
Interesses do aluno: {interesses}
Dica de adaptação: {style_hint}

Crie um exemplo prático de '{topic}' personalizado para este aluno.

Aqui está um modelo de como estruturar:
---
Contexto: Um estudante quer calcular a média das suas notas.
Exemplo:
  notas = [7.5, 8.0, 9.0]
  media = sum(notas) / len(notas)
  print(f"Média: {{media}}")
O que cada parte faz:
  - `sum(notas)`: soma todos os valores
  - `len(notas)`: conta quantas notas existem
  - `/`: divide para obter a média
Variação: tente calcular apenas a maior nota.
---

Agora crie um exemplo diferente sobre '{topic}', conectando com os interesses do aluno.
{format_instruction}
Restrição: use apenas exemplos reais e funcionais, em português do Brasil.\
"""

# ─────────────────────────────────────────────────────────────────────────────
# REFLECTION
# ─────────────────────────────────────────────────────────────────────────────

REFLECTION_V1 = """\
Aluno: {nome} | Nível: {nivel}

Crie 3 perguntas de reflexão sobre '{topic}'.\
"""

REFLECTION_V2 = """\
Aluno: {nome}, {idade} anos | Nível: {nivel} | Estilo: {estilo_aprendizado}
Interesses: {interesses}

Crie perguntas de reflexão sobre '{topic}' que estimulem este aluno a pensar criticamente.
As perguntas devem conectar o tema com a realidade e os interesses do aluno.

{format_instruction}
Gradação: a primeira pergunta deve ser mais simples, a última mais desafiadora.
Restrição: perguntas abertas, sem respostas prontas, em português do Brasil.\
"""

# ─────────────────────────────────────────────────────────────────────────────
# VISUAL
# ─────────────────────────────────────────────────────────────────────────────

VISUAL_V1 = """\
Aluno: {nome} | Nível: {nivel}

Crie uma representação visual textual de '{topic}'.\
"""

VISUAL_V2 = """\
Aluno: {nome}, {idade} anos | Nível: {nivel} | Estilo: {estilo_aprendizado}
Dica de adaptação: {style_hint}

Crie uma explicação visual e analógica de '{topic}' adaptada para este aluno.

{format_instruction}
A analogia deve usar algo familiar para um jovem de {idade} anos com interesse em {interesses}.
Restrição: use apenas analogias do cotidiano, sem termos técnicos não explicados, em português do Brasil.\
"""

# ─────────────────────────────────────────────────────────────────────────────
# Registro central de versões
# ─────────────────────────────────────────────────────────────────────────────

VERSIONS: dict[str, dict[str, str]] = {
    "conceptual": {"v1": CONCEPTUAL_V1, "v2": CONCEPTUAL_V2},
    "examples":   {"v1": EXAMPLES_V1,   "v2": EXAMPLES_V2},
    "reflection": {"v1": REFLECTION_V1, "v2": REFLECTION_V2},
    "visual":     {"v1": VISUAL_V1,     "v2": VISUAL_V2},
}
