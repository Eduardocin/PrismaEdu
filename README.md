# 🔷 PrismaEdu

Plataforma educativa que gera conteúdo personalizado para alunos usando a **API do Google Gemini**.  
O conteúdo é adaptado ao perfil de cada aluno — nível, estilo de aprendizado e interesses — por meio de técnicas avançadas de prompt engineering.

---

## Sumário

1. [Descrição do projeto](#1-descrição-do-projeto)
2. [Arquitetura](#2-arquitetura)
3. [Setup](#3-setup)
4. [Como usar a interface](#4-como-usar-a-interface)
5. [Exemplos de output](#5-exemplos-de-output)
6. [Técnicas de prompt utilizadas](#6-técnicas-de-prompt-utilizadas)
7. [Deploy no Hugging Face Spaces](#7-deploy-no-hugging-face-spaces)
8. [Como rodar os testes](#8-como-rodar-os-testes)

---

## 1. Descrição do projeto

O **Prisma** pega um tópico qualquer (ex: *"decoradores em Python"*) e gera 4 tipos de conteúdo educativo:

| Tipo | Descrição |
|---|---|
| **Conceitual** | Definição + por que importa + passo a passo + resumo |
| **Exemplos** | Código funcional contextualizado aos interesses do aluno |
| **Reflexão** | 3 perguntas críticas em gradação crescente de dificuldade |
| **Visual** | Analogia do cotidiano + representação textual/ASCII + legenda |

Cada geração é personalizada com base no perfil do aluno (`students.json`) e armazenada localmente com timestamp.

---

## 2. Arquitetura

```
PrismaEdu/
├── interface.py              # Interface Gradio (entry point da UI)
├── app.py                    # Entry point para deploy (Hugging Face Spaces)
├── requirements.txt
├── app/
│   ├── generators/           # Um módulo por tipo de conteúdo
│   │   ├── _base.py          # Pipeline: cache → prompt → API → validação → output
│   │   ├── conceptual.py
│   │   ├── examples.py
│   │   ├── reflection.py
│   │   └── visual.py
│   ├── profiles/
│   │   ├── profile_manager.py  # Carrega e busca perfis
│   │   └── students.json       # Dados dos alunos
│   ├── prompts/
│   │   ├── base_prompts.py     # SYSTEM_PERSONA, FORMAT_*, STYLE_HINTS
│   │   ├── prompt_builder.py   # Monta (system, prompt, schema) dinamicamente
│   │   ├── prompt_versions.py  # Templates v1 e v2 por content_type
│   │   └── schemas.py          # Modelos Pydantic de output
│   ├── services/
│   │   ├── gemini_client.py    # Wrapper da API Gemini
│   │   └── cache.py            # Cache JSON por hash SHA-256
│   └── storage/
│       ├── output_manager.py   # Persiste outputs com timestamp
│       └── outputs/            # Resultados gerados
├── samples/                  # Exemplos de output para referência
└── tests/
    └── test_prompts.py       # 18 testes (prompts, cache, output_manager)
```

**Fluxo de uma geração:**

```
Interface → generator → _base.run_generator()
                              │
                    ┌─────────▼─────────┐
                    │  1. Verifica cache │
                    └─────────┬─────────┘
                              │ miss
                    ┌─────────▼──────────────┐
                    │  2. build_prompt()      │
                    │  (system + user + schema)│
                    └─────────┬──────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  3. gemini_client   │
                    │  generate()         │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  4. Valida Pydantic │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  5. Salva cache     │
                    │  6. Persiste output │
                    └────────────────────┘
```

---

## 3. Setup

### Pré-requisitos

- Python 3.11+
- Chave de API do [Google AI Studio](https://aistudio.google.com/apikey)

### Passo a passo

**1. Clone o repositório**

```bash
git clone https://github.com/seu-usuario/PrismaEdu.git
cd PrismaEdu
```

**2. Crie e ative o ambiente virtual**

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

**4. Configure a chave de API**

Crie um arquivo `.env` na raiz do projeto:

```env
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash-lite   # opcional, este é o padrão
```

**5. Inicie a interface**

```bash
python interface.py
```

Acesse em: `http://localhost:7860`

---

## 4. Como usar a interface

### Aba — Gerar Conteúdo

1. Selecione o **aluno** no dropdown
2. Digite o **tópico** (ex: `funções em Python`, `fotossíntese`, `Segunda Guerra Mundial`)
3. Escolha o **tipo de conteúdo**: Conceitual / Exemplos / Reflexão / Visual
4. Selecione a **versão do prompt**: `v1` (básico) ou `v2` (personalizado)
5. Clique em **✨ Gerar Conteúdo**

### Aba — Comparar v1 vs v2

Gera o mesmo conteúdo com ambas as versões lado a lado — útil para analisar o impacto das técnicas de prompt engineering.

1. Configure aluno, tópico e tipo de conteúdo
2. Clique em **⚖️ Comparar v1 vs v2**
3. Veja os resultados em colunas paralelas

---

## 5. Exemplos de output

### Conceptual — Larissa Mendes / "decoradores em Python" (v2)

```json
{
  "definition": "Decoradores em Python são uma forma elegante de estender ou modificar
  o comportamento de funções de maneira declarativa, sem alterar seu código-fonte original.",

  "why_it_matters": "Compreender decoradores é crucial para escrever código Python mais
  limpo e reutilizável. São amplamente usados em Flask, Django e bibliotecas de ML.",

  "steps": [
    "Imagine uma receita de bolo — um decorador é uma instrução extra que você 'cola'
     na receita sem precisar reescrevê-la...",
    "A sintaxe @nome_do_decorador é um atalho: @meu_decorador acima de minha_funcao
     equivale a minha_funcao = meu_decorador(minha_funcao)...",
    "Exemplo prático: um decorador logar_chamada que imprime mensagens antes e depois
     de executar a função decorada..."
  ],

  "summary": "Decoradores são funções de ordem superior que 'envelopam' outras funções
  para adicionar funcionalidades extras de forma limpa e reutilizável."
}
```

> Output completo em [`samples/student_003/conceptual/`](samples/student_003/conceptual/)

---

## 6. Técnicas de prompt utilizadas

| Técnica | Onde é usada | Efeito |
|---|---|---|
| **Persona Prompting** | Todos os generators (v2) | Tom didático, linguagem acessível |
| **Context Setting** | Todos os generators (v2) | Adaptação ao perfil do aluno |
| **Chain-of-Thought** | `conceptual.py` | Sequência lógica nos passos |
| **Output Formatting** | Todos os generators (v2) | Estrutura consistente (Pydantic) |
| **Few-Shot** | `examples.py` | Padrão de qualidade para exemplos |
| **Inline Restrictions** | Todos os generators (v2) | Evita alucinações e desvios de idioma |
| **Style Hint** | `conceptual.py`, `visual.py` | Formato adaptado ao estilo de aprendizado |

Documentação completa com exemplos reais de input/output e análise comparativa:  
📄 [PROMPT_ENGINEERING_NOTES.md](PROMPT_ENGINEERING_NOTES.md)

---

## 7. Deploy no Hugging Face Spaces

### Pré-requisitos

- Conta no [Hugging Face](https://huggingface.co)
- Repositório público ou privado no GitHub com o projeto

### Passo a passo

**1. Crie um novo Space**

Acesse [huggingface.co/new-space](https://huggingface.co/new-space) e configure:
- **SDK:** Gradio
- **Visibilidade:** Public ou Private

**2. Conecte ao repositório GitHub**

No painel do Space, vá em **Files** e faça o upload ou conecte via Git:

```bash
# Adicione o remote do HF Spaces
git remote add space https://huggingface.co/spaces/SEU_USUARIO/NOME_DO_SPACE

# Envie o código
git push space main
```

**3. Configure o Secret da API**

No painel do Space: **Settings → Variables and secrets → New secret**

| Nome | Valor |
|---|---|
| `GEMINI_API_KEY` | sua chave do Google AI Studio |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` (opcional) |

> O `load_dotenv()` no `gemini_client.py` é ignorado silenciosamente quando não há arquivo `.env` — os `os.getenv()` funcionam normalmente com as variáveis de ambiente do Space.

**4. Entry point**

O HF Spaces detecta automaticamente o `app.py` na raiz e executa:

```python
# app.py — já criado na raiz do projeto
from interface import build_interface

demo = build_interface()

if __name__ == "__main__":
    demo.launch()
```

**5. Acompanhe o build**

Acesse a aba **Logs** do Space para acompanhar a instalação das dependências e o start da aplicação.

### Observações importantes

- O `cache.json` e os `outputs/` são gerados em tempo de execução no filesystem efêmero do Space — **não persistem entre reinicializacões**. Para persistência em produção, considere um backend externo (ex: HF Dataset, Google Cloud Storage).
- O `pytest` no `requirements.txt` não prejudica o deploy, mas pode ser removido para reduzir o tempo de build se desejado.

---

## 8. Como rodar os testes

```bash
# Ativar o ambiente virtual primeiro
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# Rodar todos os testes
python -m pytest tests/test_prompts.py -v
```

**Cobertura atual: 18 testes**

| Módulo | Testes | O que verifica |
|---|---|---|
| `TestPromptBuilder` | 7 | Persona, contexto do aluno, schema Pydantic, v1 vs v2, erros |
| `TestCache` | 6 | Miss, hit, colisão de chaves, invalidate, persistência em disco |
| `TestOutputManager` | 5 | Criação do JSON, estrutura, campos do schema, diretórios, dest=samples |

> Os testes usam `tmp_path` + `monkeypatch` — nenhum toca o cache ou outputs reais.
