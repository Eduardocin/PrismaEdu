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

**Por que foi escolhida:** Sem contexto, o modelo gera respostas genéricas. Com nome, idade, nível, estilo de aprendizado e interesses, o Gemini adapta vocabulário, profundidade e exemplos automaticamente — a mesma explicação de "recursividade" para um iniciante de 14 anos é radicalmente diferente da de um avançado de 19 anos.

**Campos injetados:**
| Campo | Efeito no output |
|---|---|
| `nome` | Personalização e tom de proximidade |
| `idade` | Calibra maturidade dos exemplos |
| `nivel` | Define profundidade técnica |
| `estilo_aprendizado` | Direciona o formato da explicação |
| `interesses` | Ancora analogias e exemplos |
| `descricao` | Instrução fina sobre dificuldades específicas |

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
| Contexto do aluno | Ausente | Nome, nível, estilo, interesses, descrição |
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
Explique o conceito de 'decoradores em Python'.
```

### Prompt v2 (exemplo — Larissa Mendes, avançada, auditiva)

```
Aluno: Larissa Mendes, 19 anos | Nível: avançado | Estilo: auditivo
Dica de adaptação: Use narrativas, analogias e explique como se estivesse contando uma história.

Explique o conceito de 'decoradores em Python' para este aluno.

Antes de responder, pense em voz alta: o que o aluno já deve saber?
Quais obstáculos ele pode ter? Como tornar isso concreto para ele?

Estruture a resposta com:
1. Definição simples (1-2 frases)
2. Por que isso importa
3. Explicação passo a passo
4. Resumo final

Adapte a linguagem ao nível avançado e ao estilo auditivo.
Restrição: responda apenas sobre 'decoradores em Python', em português do Brasil, sem inventar fatos.
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
**Max tokens:** 400

### Prompt v1

```
Dê um exemplo prático de 'listas em Python'.
```

### Prompt v2 (exemplo — Pedro Alves, iniciante, cinestésico)

```
Aluno: Pedro Alves, 15 anos | Nível: iniciante | Estilo: cinestésico
Interesses do aluno: esportes, tecnologia
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
Variação: tente calcular apenas a maior nota.
---

Agora crie um exemplo diferente sobre 'listas em Python', conectando com os interesses do aluno.
Restrição: use apenas exemplos reais e funcionais, em português do Brasil.
```

### Diferença observada v1 → v2

- **v1** gera um exemplo genérico (geralmente `frutas = ["maçã", "banana"]`), sem conexão com o aluno.
- **v2** ancora o exemplo nos interesses do Pedro (esportes/tecnologia), usa código funcional com explicação linha a linha e propõe uma variação para fixação — padrão didático consistente com o few-shot injetado.

---

## 5. Generator: Reflection

**Arquivo:** `app/generators/reflection.py`  
**Técnicas v2:** Persona + Context Setting + Output Formatting + Gradação de dificuldade + Inline Restrictions  
**Max tokens:** 300

### Prompt v1

```
Crie 3 perguntas de reflexão sobre 'estruturas de repetição'.
```

### Prompt v2 (exemplo — Carlos Eduardo, intermediário, leitura-escrita)

```
Aluno: Carlos Eduardo, 17 anos | Nível: intermediário | Estilo: leitura-escrita
Interesses: história, filosofia

Crie perguntas de reflexão sobre 'estruturas de repetição' que estimulem este aluno
a pensar criticamente. As perguntas devem conectar o tema com a realidade e os interesses
do aluno.

Gere exatamente 3 perguntas de reflexão numeradas.
Gradação: a primeira pergunta deve ser mais simples, a última mais desafiadora.
Restrição: perguntas abertas, sem respostas prontas, em português do Brasil.
```

### Diferença observada v1 → v2

- **v1** gera 3 perguntas técnicas genéricas ("O que é um loop `for`?").
- **v2** gera perguntas em gradação crescente, conectando com os interesses do Carlos (história, filosofia): da aplicação prática até questões de reflexão filosófica sobre repetição e automação na sociedade.

---

## 6. Generator: Visual

**Arquivo:** `app/generators/visual.py`  
**Técnicas v2:** Persona + Context Setting + Style Hint + Output Formatting + Inline Restrictions  
**Max tokens:** 400

### Prompt v1

```
Crie uma representação visual textual de 'recursividade'.
```

### Prompt v2 (exemplo — Ana Beatriz, iniciante, visual)

```
Aluno: Ana Beatriz, 14 anos | Nível: iniciante | Estilo: visual
Dica de adaptação: Use diagramas textuais, tabelas, listas e representações visuais.

Crie uma explicação visual e analógica de 'recursividade' adaptada para este aluno.

Estruture a resposta com:
1. Analogia do cotidiano
2. Representação textual (tabela, lista hierárquica ou ASCII)
3. Legenda explicativa

A analogia deve usar algo familiar para uma jovem de 14 anos com interesse em arte, biologia.
Restrição: use apenas analogias do cotidiano, sem termos técnicos não explicados, em português do Brasil.
```

### Diferença observada v1 → v2

- **v1** gera um diagrama ASCII genérico de árvore binária ou código recursivo, inacessível para uma iniciante.
- **v2** ancora a analogia em arte ou biologia (ex.: espiral de uma concha, galhos de uma árvore), usa representação ASCII simplificada com legenda adaptada ao nível iniciante.

---

## 7. Análise comparativa v1 vs v2

### Dimensões avaliadas

| Critério | v1 | v2 |
|---|---|---|
| Personalização ao aluno | ✗ Nenhuma | ✓ Alta (perfil completo) |
| Consistência de formato | ✗ Livre | ✓ Estruturado (Pydantic) |
| Qualidade dos exemplos | ✗ Genéricos | ✓ Ancorados nos interesses |
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
| `conceptual.py` | 600 | 4 campos, sendo `steps` o mais extenso (3+ itens) |
| `examples.py` | 400 | Código + explicação por linha + variação |
| `reflection.py` | 300 | Apenas 3 perguntas — menor schema do projeto |
| `visual.py` | 400 | Representação ASCII + analogia + legenda |

O parâmetro flui por: `generator` → `_base.run_generator()` → `gemini_client.generate()` → `GenerateContentConfig(max_output_tokens=...)`.

## Lições Aprendidas

*(Preencher conforme o projeto evolui)*
