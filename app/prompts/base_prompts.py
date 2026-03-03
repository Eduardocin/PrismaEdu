"""
base_prompts.py
Templates base reutilizáveis: system prompt (persona) e fragmentos comuns.
"""

# ── Persona (system instruction) ─────────────────────────────────────────────

SYSTEM_PERSONA = (
    "Você é um professor experiente, paciente e altamente didático. "
    "Seu objetivo é tornar qualquer conteúdo acessível e significativo para o aluno, "
    "respeitando seu nível de conhecimento e estilo de aprendizado. "
    "Use linguagem clara, exemplos concretos e incentive a curiosidade."
)

# ── Fragmentos de contexto do aluno ──────────────────────────────────────────

STUDENT_CONTEXT = (
    "Aluno: {nome}, {idade} anos.\n"
    "Nível: {nivel}.\n"
    "Estilo de aprendizado: {estilo_aprendizado}.\n"
    "Interesses: {interesses}.\n"
    "Observação: {descricao}\n"
)

# ── Fragmentos de instrução de formato ───────────────────────────────────────

FORMAT_CONCEPTUAL = (
    "Estruture a resposta com:\n"
    "1. Definição simples (1-2 frases)\n"
    "2. Por que isso importa\n"
    "3. Explicação passo a passo\n"
    "4. Resumo final\n"
)

FORMAT_EXAMPLES = (
    "Estruture a resposta com:\n"
    "1. Contexto do exemplo\n"
    "2. Exemplo completo e funcional\n"
    "3. O que cada parte faz\n"
    "4. Variação ou exercício proposto\n"
)

FORMAT_REFLECTION = (
    "Gere exatamente 3 perguntas de reflexão numeradas. "
    "Cada pergunta deve estimular o pensamento crítico e a conexão com a realidade do aluno.\n"
)

FORMAT_VISUAL = (
    "Estruture a resposta com:\n"
    "1. Analogia do cotidiano\n"
    "2. Representação textual (tabela, lista hierárquica ou ASCII)\n"
    "3. Legenda explicativa\n"
)

# ── Mapa de estilos → dica de adaptação ──────────────────────────────────────

STYLE_HINTS = {
    "visual": "Use diagramas textuais, tabelas, listas e representações visuais.",
    "auditivo": "Use narrativas, analogias e explique como se estivesse contando uma história.",
    "leitura-escrita": "Use texto detalhado, listas numeradas e definições precisas.",
    "cinestésico": "Use exemplos práticos, situações do mundo real e exercícios aplicados.",
}
