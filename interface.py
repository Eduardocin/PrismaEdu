"""
interface.py
Interface Gradio do Prisma — plataforma educativa com geração via Gemini.

Abas:
  1. Gerar Conteúdo — geração única com seleção de aluno/tópico/tipo/versão
  2. Comparar v1 vs v2 — geração lado a lado para análise de prompts
"""

import gradio as gr
from pydantic import BaseModel

from app.profiles.profile_manager import load_profiles, get_profile_by_name
from app.generators.conceptual import generate_conceptual
from app.generators.examples import generate_examples
from app.generators.reflection import generate_reflection
from app.generators.visual import generate_visual

# ── Configurações globais ────────────────────────────────────────────────────

CONTENT_TYPE_MAP = {
    "Conceitual":  "conceptual",
    "Exemplos":    "examples",
    "Reflexão":    "reflection",
    "Visual":      "visual",
}

GENERATOR_MAP = {
    "conceptual": generate_conceptual,
    "examples":   generate_examples,
    "reflection": generate_reflection,
    "visual":     generate_visual,
}

TEMPERATURA_MAP = {
    "conceptual": 0.5,
    "examples":   0.7,
    "reflection": 0.8,
    "visual":     0.6,
}


def _student_names() -> list[str]:
    """Retorna lista de nomes de alunos para o dropdown."""
    return [s["nome"] for s in load_profiles()]


# ── Formatação do resultado ──────────────────────────────────────────────────

def _format_result(result: BaseModel | dict, content_type: str) -> str:
    """Converte o resultado do generator em texto legível para o Gradio."""
    if isinstance(result, dict):
        # v1 — resposta bruta
        return result.get("raw", "(sem resposta)")

    # v2 — Pydantic model
    if content_type == "conceptual":
        return (
            f"## Definição\n{result.definition}\n\n"
            f"## Por que importa?\n{result.why_it_matters}\n\n"
            f"## Passo a passo\n"
            + "\n".join(f"{i}. {s}" for i, s in enumerate(result.steps, 1))
            + f"\n\n## Resumo\n{result.summary}"
        )

    if content_type == "examples":
        return (
            f"## Contexto\n{result.context}\n\n"
            f"## Exemplo\n```\n{result.example}\n```\n\n"
            f"## Explicação\n"
            + "\n".join(f"- {e}" for e in result.explanation)
            + f"\n\n## Variação proposta\n{result.variation}"
        )

    if content_type == "reflection":
        return (
            "## Perguntas de reflexão\n"
            + "\n".join(f"{i}. {q}" for i, q in enumerate(result.questions, 1))
        )

    if content_type == "visual":
        return (
            f"## Analogia\n{result.analogy}\n\n"
            f"## Representação visual\n```\n{result.visual_representation}\n```\n\n"
            f"## Legenda\n{result.legend}"
        )

    return str(result)


# ── Lógica de geração ────────────────────────────────────────────────────────

def gerar_conteudo(
    student_name: str,
    topic: str,
    content_type_label: str,
    version: str,
) -> str:
    """Handler da aba 'Gerar Conteúdo'."""
    if not topic.strip():
        return "⚠️ Por favor, informe um tópico."

    profile = get_profile_by_name(student_name)
    if not profile:
        return f"⚠️ Aluno '{student_name}' não encontrado."

    content_type = CONTENT_TYPE_MAP[content_type_label]
    generator = GENERATOR_MAP[content_type]
    temperatura = TEMPERATURA_MAP[content_type]

    try:
        result = generator(profile, topic, version=version, temperature=temperatura)
        return _format_result(result, content_type)
    except Exception as e:
        return f"❌ Erro ao gerar conteúdo:\n\n```\n{e}\n```"


def comparar_versoes(
    student_name: str,
    topic: str,
    content_type_label: str,
) -> tuple[str, str]:
    """Handler da aba 'Comparar v1 vs v2'."""
    if not topic.strip():
        return "⚠️ Informe um tópico.", "⚠️ Informe um tópico."

    profile = get_profile_by_name(student_name)
    if not profile:
        msg = f"⚠️ Aluno '{student_name}' não encontrado."
        return msg, msg

    content_type = CONTENT_TYPE_MAP[content_type_label]
    generator = GENERATOR_MAP[content_type]
    temperatura = TEMPERATURA_MAP[content_type]

    resultados = []
    for version in ["v1", "v2"]:
        try:
            result = generator(profile, topic, version=version, temperature=temperatura)
            resultados.append(_format_result(result, content_type))
        except Exception as e:
            resultados.append(f"❌ Erro ({version}):\n\n```\n{e}\n```")

    return resultados[0], resultados[1]


# ── Construção da UI ─────────────────────────────────────────────────────────

def build_interface() -> gr.Blocks:
    student_names = _student_names()

    with gr.Blocks(title="Prisma — Educação Personalizada") as demo:

        gr.Markdown(
            """
            # 🔷 Prisma — Plataforma Educativa Personalizada
            Geração de conteúdo adaptado ao perfil de cada aluno via **Google Gemini**.
            """
        )

        # ── ABA 1: Gerar Conteúdo ────────────────────────────────────────────
        with gr.Tab("Gerar Conteúdo"):
            gr.Markdown("### Configure a geração")

            with gr.Row():
                dd_aluno = gr.Dropdown(
                    choices=student_names,
                    value=student_names[0],
                    label="Aluno",
                    scale=1,
                )
                txt_topico = gr.Textbox(
                    placeholder="Ex: funções em Python",
                    label="Tópico",
                    scale=2,
                )

            with gr.Row():
                dd_tipo = gr.Dropdown(
                    choices=list(CONTENT_TYPE_MAP.keys()),
                    value="Conceitual",
                    label="Tipo de conteúdo",
                    scale=1,
                )
                dd_versao = gr.Dropdown(
                    choices=["v1", "v2"],
                    value="v2",
                    label="Versão do prompt",
                    scale=1,
                )

            btn_gerar = gr.Button("✨ Gerar Conteúdo", variant="primary")

            gr.Markdown("### Resultado")
            md_output = gr.Markdown(value="_O conteúdo gerado aparecerá aqui._")

            btn_gerar.click(
                fn=gerar_conteudo,
                inputs=[dd_aluno, txt_topico, dd_tipo, dd_versao],
                outputs=md_output,
            )

        # ── ABA 2: Comparar v1 vs v2 ─────────────────────────────────────────
        with gr.Tab("Comparar v1 vs v2"):
            gr.Markdown(
                "### Comparação lado a lado\n"
                "Gera o mesmo conteúdo com **v1** e **v2** para análise de prompts."
            )

            with gr.Row():
                dd_aluno_cmp = gr.Dropdown(
                    choices=student_names,
                    value=student_names[0],
                    label="Aluno",
                    scale=1,
                )
                txt_topico_cmp = gr.Textbox(
                    placeholder="Ex: variáveis em Python",
                    label="Tópico",
                    scale=2,
                )

            dd_tipo_cmp = gr.Dropdown(
                choices=list(CONTENT_TYPE_MAP.keys()),
                value="Conceitual",
                label="Tipo de conteúdo",
            )

            btn_comparar = gr.Button("⚖️ Comparar v1 vs v2", variant="primary")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### v1 — Prompt Básico")
                    md_v1 = gr.Markdown(value="_Resultado v1 aparecerá aqui._")
                with gr.Column():
                    gr.Markdown("#### v2 — Prompt Avançado")
                    md_v2 = gr.Markdown(value="_Resultado v2 aparecerá aqui._")

            btn_comparar.click(
                fn=comparar_versoes,
                inputs=[dd_aluno_cmp, txt_topico_cmp, dd_tipo_cmp],
                outputs=[md_v1, md_v2],
            )

    return demo


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo = build_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
    )
