"""
interface.py
Interface Gradio do Prisma - Plataforma Educativa com IA.

Uso standalone: python app/interface.py
"""

import json
import concurrent.futures
from pathlib import Path

import gradio as gr

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
/* ── Header ── */
.prisma-header { text-align: center; padding: 1.2rem 1rem 0.8rem; margin-bottom: 0.5rem; }
.prisma-eyebrow { font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; opacity: 0.5; }
.prisma-title { font-size: 1.7rem; font-weight: 700; margin: 0.2rem 0; }
.prisma-title span { color: #2D6BE4; }
.prisma-subtitle { font-size: 0.88rem; opacity: 0.6; }

/* ── Chips de perfil ── */
.profile-chips { display: flex; flex-wrap: wrap; gap: 5px; padding: 6px 0; }
.chip { font-size: 0.71rem; padding: 2px 9px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.15); white-space: nowrap; }
.badge-iniciante     { color: #276133; background: #D4EDDA; border-color: #B8DACC; }
.badge-intermediario { color: #856404; background: #FFF3CD; border-color: #F5E07F; }
.badge-avancado      { color: #0C5299; background: #CCE5FF; border-color: #99C9FF; }

/* ── Footer ── */
.prisma-footer { text-align: center; padding: 0.8rem; margin-top: 1rem; font-size: 0.7rem; opacity: 0.4; }
"""

# ── Constantes ────────────────────────────────────────────────────────────────

CONTENT_TYPES: dict[str, str] = {
    "Explicacao Conceitual": "conceptual",
    "Exemplos Praticos":     "examples",
    "Perguntas de Reflexao": "reflection",
    "Resumo Visual":         "visual",
}

NIVEL_BADGE_CLASS: dict[str, str] = {
    "iniciante":     "badge-iniciante",
    "intermediario": "badge-intermediario",
    "avancado":      "badge-avancado",
}

NIVEIS  = ["iniciante", "intermediario", "avancado"]
ESTILOS = ["visual", "auditivo", "leitura-escrita", "cinestetico"]

# ── Montagem de perfil ────────────────────────────────────────────────────────

def _build_profile(nome: str, idade, nivel: str, estilo: str) -> dict:
    return {
        "id": f"user_{nome.lower().replace(' ', '_')}",
        "nome": nome.strip(),
        "idade": int(idade) if str(idade).strip().isdigit() else 0,
        "centro": "",
        "nivel": nivel,
        "estilo_aprendizado": estilo,
        "interesses": [],
        "descricao": "",
    }

# ── Formatacao de resultado ───────────────────────────────────────────────────

def _format_result(result: object) -> str:
    if result is None:
        return "_Nenhum conteudo gerado._"
    if isinstance(result, dict):
        return result.get("raw", str(result))
    cls_name = type(result).__name__
    if cls_name == "ConceptualResponse":
        lines = [
            f"## Definicao\n{result.definition}",
            f"## Por que importa?\n{result.why_it_matters}",
            "## Passo a passo\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(result.steps)),
            f"## Resumo\n{result.summary}",
        ]
        return "\n\n".join(lines)
    if cls_name == "ExamplesResponse":
        lines = [
            f"## Contexto\n{result.context}",
            f"## Exemplo\n```\n{result.example}\n```",
            "## O que cada parte faz\n" + "\n".join(f"- {e}" for e in result.explanation),
            f"## Variacao / Exercicio\n{result.variation}",
        ]
        return "\n\n".join(lines)
    if cls_name == "ReflectionResponse":
        qs = "\n".join(f"{i+1}. {q}" for i, q in enumerate(result.questions))
        return f"## Perguntas de Reflexao\n\n{qs}"
    if cls_name == "VisualResponse":
        lines = [
            f"## Analogia\n{result.analogy}",
            f"## Representacao Visual\n```\n{result.visual_representation}\n```",
            f"## Legenda\n{result.legend}",
        ]
        return "\n\n".join(lines)
    try:
        data = result.model_dump()
        return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"
    except Exception:
        return str(result)


# ── Funcoes de geracao ────────────────────────────────────────────────────────

def _get_generator_fn(content_type_key: str):
    ct = CONTENT_TYPES[content_type_key]
    if ct == "conceptual":
        from app.generators.conceptual import generate_conceptual
        return generate_conceptual
    if ct == "examples":
        from app.generators.examples import generate_examples
        return generate_examples
    if ct == "reflection":
        from app.generators.reflection import generate_reflection
        return generate_reflection
    if ct == "visual":
        from app.generators.visual import generate_visual
        return generate_visual
    raise ValueError(f"Tipo desconhecido: {ct}")


def generate_content(
    nome: str, idade, nivel: str, estilo: str,
    topic: str, content_type_key: str, version: str,
) -> str:
    if not nome or not nome.strip():
        return "_Por favor, preencha o nome do aluno._"
    if not topic or not topic.strip():
        return "_Por favor, insira um topico._"
    profile = _build_profile(nome, idade, nivel, estilo)
    try:
        fn = _get_generator_fn(content_type_key)
        result = fn(profile=profile, topic=topic.strip(), version=version)
        return _format_result(result)
    except Exception as exc:
        return (
            f"**Erro ao gerar conteudo.**\n\n`{exc}`\n\n"
            "_Verifique se GEMINI_API_KEY esta configurada._"
        )


def generate_both_versions(
    nome: str, idade, nivel: str, estilo: str,
    topic: str, content_type_key: str,
) -> tuple[str, str]:
    if not nome or not nome.strip():
        msg = "_Por favor, preencha o nome do aluno._"
        return msg, msg
    if not topic or not topic.strip():
        msg = "_Por favor, insira um topico._"
        return msg, msg
    profile = _build_profile(nome, idade, nivel, estilo)

    def _call(ver: str) -> str:
        try:
            fn = _get_generator_fn(content_type_key)
            result = fn(profile=profile, topic=topic.strip(), version=ver)
            return _format_result(result)
        except Exception as exc:
            return f"**Erro.**\n\n`{exc}`"

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fut_v1 = pool.submit(_call, "v1")
        fut_v2 = pool.submit(_call, "v2")
        return fut_v1.result(), fut_v2.result()


# ── HTML helpers ──────────────────────────────────────────────────────────────

def _student_chips_html(nome: str, idade, nivel: str, estilo: str) -> str:
    if not nome or not nome.strip():
        return ""
    badge_cls = NIVEL_BADGE_CLASS.get(nivel, "")
    return f"""
<div class="profile-chips">
  <span class="chip">{idade} anos</span>
  <span class="chip {badge_cls} badge">{nivel}</span>
  <span class="chip">{estilo}</span>
</div>
"""


# ── Build Interface ───────────────────────────────────────────────────────────

def _student_form() -> tuple:
    nome   = gr.Textbox(label="Nome do aluno", placeholder="ex.: Ana Beatriz")
    idade  = gr.Number(label="Idade", value=18, minimum=1, maximum=99, precision=0)
    nivel  = gr.Dropdown(choices=NIVEIS, value="intermediario", label="Nivel", interactive=True)
    estilo = gr.Dropdown(choices=ESTILOS, value="visual", label="Estilo de aprendizado", interactive=True)
    return nome, idade, nivel, estilo


def build_interface() -> gr.Blocks:
    content_type_choices = list(CONTENT_TYPES.keys())

    with gr.Blocks(css=CSS, title="Prisma - Plataforma Educativa") as demo:

        gr.HTML(value="""
<div class="prisma-header">
  <div class="prisma-eyebrow">Plataforma Educativa - UFPE</div>
  <h1 class="prisma-title"><span>Prisma</span> - Conteudo Personalizado com IA</h1>
  <p class="prisma-subtitle">Explicacoes adaptadas ao perfil de cada aluno via Google Gemini</p>
</div>""", container=False)

        with gr.Tabs():

            with gr.TabItem("Gerador"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=280):
                        gr.Markdown("### Perfil do aluno")
                        txt_nome, num_idade, dd_nivel, dd_estilo = _student_form()
                        chips_html = gr.HTML(container=False)

                        gr.Markdown("### Conteudo")
                        txt_topic    = gr.Textbox(label="Topico", placeholder="ex.: fotossintese, fracoes, Segunda Guerra...", lines=2)
                        dd_content   = gr.Dropdown(choices=content_type_choices, value=content_type_choices[0], label="Tipo de conteudo", interactive=True)
                        dd_version   = gr.Dropdown(
                            choices=[("Personalizado", "v2"), ("Direto", "v1")],
                            value="v2",
                            label="Versao do prompt",
                            interactive=True,
                        )
                        btn_generate = gr.Button("Gerar Conteudo", variant="primary", size="lg")

                    with gr.Column(scale=2):
                        md_output = gr.Markdown(value="_Preencha os campos e clique em Gerar Conteudo_", label="Resultado")

                _profile_inputs = [txt_nome, num_idade, dd_nivel, dd_estilo]

                for field in _profile_inputs:
                    field.change(fn=_student_chips_html, inputs=_profile_inputs, outputs=[chips_html])

                btn_generate.click(
                    fn=generate_content,
                    inputs=_profile_inputs + [txt_topic, dd_content, dd_version],
                    outputs=[md_output],
                )

            with gr.TabItem("Comparar Prompts"):
                gr.Markdown("### Perfil do aluno")
                with gr.Row():
                    cmp_nome, cmp_idade, cmp_nivel, cmp_estilo = _student_form()

                with gr.Row():
                    txt_cmp_topic  = gr.Textbox(label="Topico", placeholder="ex.: derivadas, fotossintese...", lines=1)
                    dd_cmp_content = gr.Dropdown(choices=content_type_choices, value=content_type_choices[0], label="Tipo de conteudo", interactive=True)

                btn_compare = gr.Button("Comparar: Prompt Direto vs Personalizado", variant="primary", size="lg")

                with gr.Row():
                    md_v1 = gr.Markdown(value="_Aguardando comparacao..._", label="Prompt Direto")
                    md_v2 = gr.Markdown(value="_Aguardando comparacao..._", label="Prompt Personalizado")

                btn_compare.click(
                    fn=generate_both_versions,
                    inputs=[cmp_nome, cmp_idade, cmp_nivel, cmp_estilo,
                            txt_cmp_topic, dd_cmp_content],
                    outputs=[md_v1, md_v2],
                )

        gr.HTML(value='<div class="prisma-footer">Prisma - Plataforma Educativa com IA - Powered by Google Gemini</div>', container=False)

    return demo


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    demo = build_interface()
    demo.launch()
