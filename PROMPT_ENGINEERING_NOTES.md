# Prompt Engineering Notes — PrismaEdu

Documentação das decisões de prompt engineering do projeto Prisma.  
Cada técnica foi escolhida com base em seu impacto direto na qualidade pedagógica do output.

---

## Sumário

1. [Técnicas utilizadas e motivação](#1-técnicas-utilizadas-e-motivação)
2. [Arquitetura de prompts — v1 vs v2](#2-arquitetura-de-prompts--v1-vs-v2)
3. [Generator: Conceptual](#3-generator-conceptual)
4. [Generator: Examples](#4-generator-examples)
5. [Generator: Reflection](#5-generator-reflection)
6. [Generator: Visual](#6-generator-visual)
7. [Análise comparativa v1 vs v2](#7-análise-comparativa-v1-vs-v2)
8. [Controle de tokens](#8-controle-de-tokens)
9. [Conciseness constraints e JSON safety](#9-conciseness-constraints-e-json-safety)

---

## 1. Técnicas utilizadas e motivação

### Persona Prompting

**O que é:** Definição explícita do papel do modelo no `system_instruction`.

**Por que foi escolhida:** O Gemini, como qualquer LLM, ajusta tom, vocabulário e profundidade de acordo com a persona atribuída. Ao declarar *"Você é um professor experiente, paciente e altamente didático"*, o modelo passa a gerar respostas com linguagem acessível, encorajamento ao aluno e foco em clareza — comportamentos que não emergem de forma consistente em prompts neutros.

**Onde está:** `app/prompts/base_prompts.py` → `SYSTEM_PERSONA`

```
"Você é um professor experiente, paciente e altamente didático.
Seu objetivo é tornar qualquer conteúdo acessível e significativo para o aluno,
respeitando seu nível de conhecimento e estilo de aprendizado.
Use linguagem clara, exemplos concretos e incentive a curiosidade."
```

---

### Context Setting

**O que é:** Injeção do perfil completo do aluno no início de cada prompt.

**Por que foi escolhida:** Sem contexto, o modelo gera respostas genéricas. Com nome, idade, nível e estilo de aprendizado fornecidos pelo usuário na interface, o Gemini adapta vocabulário, profundidade e exemplos automaticamente — a mesma explicação de “recursividade” para um iniciante de 14 anos é radicalmente diferente da de um avançado de 19 anos.

**Campos injetados:**
| Campo | Efeito no output |
|---|---|
| `nome` | Personalização e tom de proximidade |
| `idade` | Calibra maturidade dos exemplos |
| `nivel` | Define profundidade técnica |
| `estilo_aprendizado` | Direciona o formato da explicação |
| `descricao` | Instrução fina sobre dificuldades específicas (vazio por padrão) |

---

### Chain-of-Thought (CoT)

**O que é:** Instrução para o modelo "pensar em voz alta" antes de responder.

**Por que foi escolhida:** Em tarefas educativas, o raciocínio intermediário melhora a coerência pedagógica. A instrução *"Antes de responder, pense em voz alta: o que o aluno já deve saber? Quais obstáculos ele pode ter?"* força o modelo a planejar a explicação, resultando em passos mais ordenados e sem saltos lógicos.

**Aplicado em:** `conceptual.py` (único generator onde a sequência lógica é crítica)

---

### Output Formatting

**O que é:** Instrução explícita da estrutura esperada, reforçada por Output Schema (Pydantic).

**Por que foi escolhida:** Dupla camada de controle:
1. O fragmento `FORMAT_*` no prompt descreve a estrutura em linguagem natural
2. O schema Pydantic valida e força o JSON estruturado via `response_schema` da API

Isso elimina respostas em prosa livre, garante campos previsíveis e permite renderização consistente na interface.

---

### Few-Shot

**O que é:** Inclusão de um exemplo concreto dentro do prompt.

**Por que foi escolhida:** No generator de exemplos, o modelo precisa entender o nível de granularidade esperado (não basta "dê um exemplo" — é preciso mostrar o padrão: contexto + código + explicação linha a linha + variação proposta). O few-shot interno garante esse padrão sem precisar de múltiplas tentativas.

**Aplicado em:** `examples.py`

---

### Inline Restrictions

**O que é:** Restrições simples no final de cada template v2.

**Por que foram escolhidas:** LLMs tendem a alucinar, misturar idiomas ou desviar do tópico. Restrições como *"Restrição: responda apenas sobre '{topic}', em português do Brasil, sem inventar fatos"* funcionam como guardrails leves — sem overhead de validação externa.

---

### Conciseness Constraints (todos os prompts — v1 e v2)

**O que é:** Instrução de brevidade adicionada ao final de **todos** os templates (v1 e v2) de todos os generators.

**Texto exato:**
```
Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

**Por que foi necessária:** O Gemini, sem essa instrução, pode gerar respostas extensas que atingem o `max_output_tokens` antes de fechar o JSON — causando truncamento silencioso. A instrução atua em duas frentes:
1. **Redução preventiva** — o modelo limita o próprio output antes de atingir o limite de tokens
2. **JSON safety** — lembra o modelo de fechar o objeto JSON mesmo em respostas mais curtas

**Complemento no código:** A função `_safe_parse` em `app/generators/_parsers.py` detecta JSON truncado (`_is_truncated`) e retorna `{"truncated": True}` em vez de lançar exceção, enquanto a interface exibe um alerta ⚠️ orientando o usuário a usar um tópico mais específico.

---

### Style Hint Adaptativo

**O que é:** Dica de adaptação baseada no `estilo_aprendizado` do aluno, mapeada em `STYLE_HINTS`.

**Por que foi escolhida:** Cada estilo de aprendizado tem um formato de output ideal. Em vez de prompt genérico, o `style_hint` injeta uma instrução específica:

| Estilo | Dica injetada |
|---|---|
| `visual` | "Use diagramas textuais, tabelas, listas e representações visuais." |
| `auditivo` | "Use narrativas, analogias e explique como se estivesse contando uma história." |
| `leitura-escrita` | "Use texto detalhado, listas numeradas e definições precisas." |
| `cinestésico` | "Use exemplos práticos, situações do mundo real e exercícios aplicados." |

---

## 2. Arquitetura de prompts — v1 vs v2

| Dimensão | v1 | v2 |
|---|---|---|
| System instruction | Vazia (`""`) | `SYSTEM_PERSONA` completa |
| Contexto do aluno | Ausente | Nome, nível, estilo, descrição |
| Técnica principal | Nenhuma | CoT / Few-Shot / Style Hint (por tipo) |
| Formato da resposta | Livre (prosa) | `FORMAT_*` + Output Schema Pydantic |
| Restrições | Nenhuma | Inline restrictions ao final |
| Output schema | `None` (texto bruto) | Modelo Pydantic validado |
| Retorno do generator | `{"raw": str}` | Instância Pydantic |

---

## 3. Generator: Conceptual

**Arquivo:** `app/generators/conceptual.py`  
**Técnicas v2:** Persona + Context Setting + Chain-of-Thought + Output Formatting + Inline Restrictions  
**Max tokens:** 600

### Prompt v1

```
Aluno: {nome} | Nível: {nivel}

Explique o conceito de '{topic}' de forma clara e direta.

Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

### Prompt v2 (exemplo — Larissa Mendes, avançada, auditiva)

```
Aluno: Larissa Mendes, 19 anos | Nível: avançado | Estilo: auditivo
Dica de adaptação: Use narrativas, analogias e explique como se estivesse contando uma história.

Explique o conceito de 'decoradores em Python' para este aluno.

Antes de responder, pense em voz alta: o que o aluno já deve saber?
Quais obstáculos ele pode ter? Como tornar isso concreto para ele?

{format_instruction}
Adapte a linguagem ao nível avançado e ao estilo auditivo.
Restrição: responda apenas sobre 'decoradores em Python', em português do Brasil, sem inventar fatos.

Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

### Output v2 real — Larissa Mendes / "decoradores em Python"

```json
{
  "definition": "Decoradores em Python são uma forma elegante de estender ou modificar o
  comportamento de funções ou métodos de maneira declarativa, sem alterar seu código-fonte
  original. Eles funcionam como 'envoltórios' que adicionam funcionalidades antes ou depois
  da execução da função decorada.",

  "why_it_matters": "Compreender decoradores é crucial para escrever código Python mais limpo,
  reutilizável e expressivo. Eles são amplamente utilizados em frameworks web (como Flask e
  Django) para tarefas como autenticação, logging e caching...",

  "steps": [
    "Imagine que você tem uma função principal, como uma receita de bolo. Um decorador é como
    uma instrução adicional que você 'cola' na sua receita sem precisar reescrevê-la inteira...",
    "A sintaxe @nome_do_decorador é um atalho mágico. Quando você escreve @meu_decorador acima
    da definição de minha_funcao, o Python automaticamente executa
    minha_funcao = meu_decorador(minha_funcao)...",
    "Vamos a um exemplo prático: um decorador logar_chamada que imprime mensagens antes e
    depois de executar a função decorada..."
  ],

  "summary": "Decoradores são funções de ordem superior que nos permitem 'envelopar' outras
  funções para adicionar funcionalidades extras de forma limpa e reutilizável..."
}
```

### Diferença observada v1 → v2

- **v1** retorna texto contínuo sem estrutura, sem ancoragem ao perfil do aluno.
- **v2** produz campos separados (`definition`, `why_it_matters`, `steps`, `summary`), linguagem narrativa adaptada ao estilo auditivo da Larissa, com analogia da receita de bolo e profundidade adequada ao nível avançado.

---

## 4. Generator: Examples

**Arquivo:** `app/generators/examples.py`  
**Técnicas v2:** Persona + Context Setting + Few-Shot + Output Formatting + Inline Restrictions  
**Max tokens:** 1200

### Prompt v1

```
Aluno: {nome} | Nível: {nivel}

Dê um exemplo prático de '{topic}'.

Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

### Prompt v2 (exemplo — Pedro Alves, iniciante, cinestésico)

```
Aluno: Pedro Alves, 15 anos | Nível: iniciante | Estilo: cinestésico
Dica de adaptação: Use exemplos práticos, situações do mundo real e exercícios aplicados.

Crie um exemplo prático de 'listas em Python' personalizado para este aluno.

Aqui está um modelo de como estruturar:
---
Contexto: Um estudante quer calcular a média das suas notas.
Exemplo:
  notas = [7.5, 8.0, 9.0]
  media = sum(notas) / len(notas)
  print(f"Média: {media}")
O que cada parte faz:
  - `sum(notas)`: soma todos os valores
  - `len(notas)`: conta quantas notas existem
  - `/`: divide para obter a média
Variação: tente calcular apenas a maior nota.
---

Agora crie um exemplo diferente sobre 'listas em Python', adaptado ao estilo cinestésico deste aluno.
{format_instruction}
Restrição: use apenas exemplos reais e funcionais, em português do Brasil.

Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

### Diferença observada v1 → v2

- **v1** gera um exemplo genérico (geralmente `frutas = ["maçã", "banana"]`), sem conexão com o aluno.
- **v2** usa código funcional com explicação linha a linha e propõe uma variação para fixação — padrão didático consistente com o few-shot injetado.

---

## 5. Generator: Reflection

**Arquivo:** `app/generators/reflection.py`  
**Técnicas v2:** Persona + Context Setting + Output Formatting + Gradação de dificuldade + Inline Restrictions  
**Max tokens:** 300

### Prompt v1

```
Aluno: {nome} | Nível: {nivel}

Crie 3 perguntas de reflexão sobre '{topic}'.

Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

### Prompt v2 (exemplo — Carlos Eduardo, intermediário, leitura-escrita)

```
Aluno: Carlos Eduardo, 17 anos | Nível: intermediário | Estilo: leitura-escrita

Crie perguntas de reflexão sobre 'estruturas de repetição' que estimulem este aluno
a pensar criticamente.
As perguntas devem conectar o tema com a realidade e o dia a dia do aluno.

{format_instruction}
Gradação: a primeira pergunta deve ser mais simples, a última mais desafiadora.
Restrição: perguntas abertas, sem respostas prontas, em português do Brasil.

Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

### Diferença observada v1 → v2

- **v1** gera 3 perguntas técnicas genéricas ("O que é um loop `for`?").
- **v2** gera perguntas em gradação crescente, da aplicação prática até questões de reflexão filosófica sobre repetição e automação na sociedade.

---

## 6. Generator: Visual

**Arquivo:** `app/generators/visual.py`  
**Técnicas v2:** Persona + Context Setting + Style Hint + Output Formatting + ASCII Constraints + Inline Restrictions  
**Max tokens:** 1200

### Prompt v1

```
Aluno: {nome} | Nível: {nivel}

Crie uma representação visual textual de '{topic}'.

Regras para o diagrama ASCII:
- O diagrama ASCII deve ter no máximo 8 linhas
- Cada linha deve ter no máximo 60 caracteres
- Use setas simples: -->, |, v, ^
- Não use caixas complexas com bordas duplas
- O campo visual_representation deve estar completo e fechado

Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

### Prompt v2 (exemplo — Ana Beatriz, iniciante, visual)

```
Aluno: Ana Beatriz, 14 anos | Nível: iniciante | Estilo: visual
Dica de adaptação: Use diagramas textuais, tabelas, listas e representações visuais.

Crie uma explicação visual e analógica de 'recursividade' adaptada para este aluno.

{format_instruction}
A analogia deve usar algo familiar para uma jovem de 14 anos no nível iniciante.
Adapte a analogia para o estilo visual do aluno.
A analogia deve ter no máximo 3 frases curtas.
Restrição: use apenas analogias do cotidiano, sem termos técnicos não explicados, em português do Brasil.

Regras para o diagrama ASCII:
- O diagrama ASCII deve ter no máximo 8 linhas
- Cada linha deve ter no máximo 60 caracteres
- Use setas simples: -->, |, v, ^
- Não use caixas complexas com bordas duplas
- O campo visual_representation deve estar completo e fechado

Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```

### Restrições de diagrama ASCII

Adicionadas explicitamente em v1 e v2 após diagnóstico de outputs com diagramas extensos e mal renderizados no Markdown:

| Restrição | Motivo |
|---|---|
| Máx 8 linhas | Evita scroll excessivo na interface |
| Máx 60 chars/linha | Garante renderização sem quebra em telas menores |
| Setas simples (`-->`, `\|`, `v`, `^`) | Compatibilidade universal com Markdown |
| Sem bordas duplas | Caracteres `═`, `╔`, `╗` quebram em alguns terminais/browsers |
| Campo `visual_representation` completo | Instrução explícita contra truncamento do campo mais longo |

### Diferença observada v1 → v2

- **v1** gera um diagrama ASCII genérico de árvore binária ou código recursivo, inacessível para uma iniciante. Com as restrições, o diagrama é curto e usa setas simples.
- **v2** ancora a analogia em algo familiar (ex.: espiral de uma concha, galhos de uma árvore), limita a analogia a 3 frases curtas, adapta ao estilo do aluno e produz representação ASCII dentro dos limites definidos.

---

## 7. Análise comparativa v1 vs v2

### Dimensões avaliadas

| Critério | v1 | v2 |
|---|---|---|
| Personalização ao aluno | ✗ Nenhuma | ✓ Alta (perfil completo) |
| Consistência de formato | ✗ Livre | ✓ Estruturado (Pydantic) |
| Qualidade dos exemplos | ✗ Genéricos | ✓ Adaptados ao nível e estilo |
| Profundidade adequada ao nível | ✗ Fixa | ✓ Adaptada (iniciante→avançado) |
| Conectividade com o cotidiano | ✗ Técnico | ✓ Analogias personalizadas |
| Gradação de dificuldade | ✗ Ausente | ✓ Presente (reflection) |
| Rastreabilidade do output | ✗ Texto bruto | ✓ Campos nomeados |
| Integrabilidade na interface | ✗ Difícil | ✓ Direto (atributos Pydantic) |

### Quando usar v1

v1 é útil para **prototipagem rápida**, benchmarking da linha de base ou quando o custo de tokens é o principal fator. O output bruto também pode ser útil para análise do comportamento padrão do modelo sem intervenção.

### Conclusão

A v2 representa um salto qualitativo em todas as dimensões educacionais relevantes. O investimento em tokens extras (persona + contexto) é compensado pela eliminação de pós-processamento e pela qualidade pedagógica do conteúdo gerado, que chega às mãos do aluno sem necessitar de edição humana.

---

## 8. Controle de tokens

Cada generator define um limite explícito de `max_output_tokens` repassado à API, calibrado para cobrir o schema sem excessos:

| Generator | Limite | Justificativa |
|---|---|---|
| `conceptual.py` | 1000 | 4 campos, sendo `steps` o mais extenso (3+ itens com raciocínio CoT) |
| `examples.py` | 1200 | Código + explicação linha a linha + variação (maior schema do projeto) |
| `reflection.py` | 600 | 3 perguntas com gradação — schema menor, mas perguntas contextualizadas podem ser longas |
| `visual.py` | 1200 | Representação ASCII + analogia + legenda; campo `visual_representation` pode ser extenso |

O parâmetro flui por: `generator` → `_base.run_generator()` → `gemini_client.generate()` → `GenerateContentConfig(max_output_tokens=...)`.

---

## 9. Conciseness constraints e JSON safety

### Problema identificado

O Gemini pode, por padrão, gerar respostas longas demais para o `max_output_tokens` configurado, causando **truncamento silencioso** — o JSON é cortado antes de ser fechado, resultando em parse error na validação Pydantic.

### Solução em duas camadas

**Camada 1 — Instrução preventiva nos prompts (todos os templates, v1 e v2):**
```
Seja objetivo e conciso. Limite sua resposta a no máximo 600 palavras.
Prefira listas curtas a parágrafos longos.
O JSON de resposta deve estar sempre completo e fechado.
```
Instrui o modelo a se auto-limitar *antes* de atingir o limite de tokens.

**Camada 2 — Parser robusto no código (`app/generators/_parsers.py`):**

```python
def _is_truncated(raw: str) -> bool:
    """Retorna True se o JSON começa com { mas não fecha corretamente."""
    stripped = raw.strip()
    if not stripped.startswith("{"):
        return False
    return not (stripped.endswith("}") or stripped.endswith('"'))

def _safe_parse(raw: str, model_class):
    if _is_truncated(raw):
        return {"raw": raw, "truncated": True}
    try:
        return model_class.model_validate_json(raw)
    except Exception:
        pass
    # fallback: extrai bloco ```json```
    match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
    if match:
        try:
            return model_class.model_validate_json(match.group(1))
        except Exception:
            pass
    return {"raw": raw, "truncated": False}
```

**Camada 3 — Alerta na interface (`app/interface.py`):**

Quando `truncated=True`, a interface exibe:
> ⚠️ **Resposta incompleta** — o tópico gerou mais conteúdo do que o limite permite.
> Tente um tópico mais específico ou reduza o nível de detalhe.

### Fluxo completo de tratamento de truncamento

```
Gemini API
    |
    v
raw text (pode estar truncado)
    |
    v
_safe_parse(raw, schema)
    ├── _is_truncated? → {"truncated": True, "raw": ...}
    ├── model_validate_json direto? → Instância Pydantic ✓
    ├── fallback ```json```? → Instância Pydantic ✓
    └── falha total → {"truncated": False, "raw": ...}
    |
    v
_format_result(result)
    ├── truncated=True → ⚠️ alerta + conteúdo parcial
    ├── truncated=False → conteúdo bruto sem alerta
    └── Pydantic → campos formatados normalmente
```

