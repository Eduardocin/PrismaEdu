"""
interface.py
Interface Gradio do Prisma — Plataforma Educativa com IA.

Uso standalone: python app/interface.py
"""

import json
import concurrent.futures
from pathlib import Path

import gradio as gr

# ─── CSS ─────────────────────────────────────────────────────────────────────

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
.badge-iniciante    { color: #276133; background: #D4EDDA; border-color: #B8DACC; }
.badge-intermediário { color: #856404; background: #FFF3CD; border-color: #F5E07F; }
.badge-avançado     { color: #0C5299; background: #CCE5FF; border-color: #99C9FF; }

/* ── Footer ── */
.prisma-footer { text-align: center; padding: 0.8rem; margin-top: 1rem; font-size: 0.7rem; opacity: 0.4; }
"""

# ─── Constantes ──────────────────────────────────────────────────────────────

CONTENT_TYPES: dict[str, str] = {
    "💡 Explicação Conceitual": "conceptual",
    "🔬 Exemplos Práticos":     "examples",
    "🤔 Perguntas de Reflexão": "reflection",
    "🗺️ Resumo Visual":         "visual",
}

NIVEL_BADGE_CLASS: dict[str, str] = {
    "iniciante":    "badge-iniciante",
    "intermediário": "badge-intermediário",
    "avançado":     "badge-avançado",
}

# ─── Carregamento de perfis ───────────────────────────────────────────────────

def _load_profiles() -> list[dict]:
    """Carrega students.json com fallback para mocks."""
    try:
        from app.profiles.profile_manager import load_profiles
        return load_profiles()
    except Exception:
        pass
    try:
        json_path = Path(__file__).parent / "profiles" / "students.json"
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)["students"]
    except Exception:
        return [
            {
                "id": "mock_001",
                "nome": "Ana Beatriz (mock)",
                "idade": 14,
                "nivel": "iniciante",
                "estilo_aprendizado": "visual",
                "interesses": ["arte", "biologia"],
                "descricao": "Perfil de demonstração.",
            }
        ]


PROFILES: list[dict] = _load_profiles()
PROFILE_MAP: dict[str, dict] = {p["nome"]: p for p in PROFILES}

# ─── Formatação de resultado ─────────────────────────────────────────────────

def _format_result(result: object) -> str:
    """Converte qualquer resultado de generator para Markdown legível."""
    if result is None:
        return "_Nenhum conteúdo gerado._"

    # v1: dict com chave 'raw'
    if isinstance(result, dict):
        return result.get("raw", str(result))

    # Pydantic model — verificar tipo pelo nome da classe
    cls_name = type(result).__name__

    if cls_name == "ConceptualResponse":
        lines = [
            f"## Definição\n{result.definition}",
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
            f"## Variação / Exercício\n{result.variation}",
        ]
        return "\n\n".join(lines)

    if cls_name == "ReflectionResponse":
        qs = "\n".join(f"{i+1}. {q}" for i, q in enumerate(result.questions))
        return f"## Perguntas de Reflexão\n\n{qs}"

    if cls_name == "VisualResponse":
        lines = [
            f"## Analogia\n{result.analogy}",
            f"## Representação Visual\n```\n{result.visual_representation}\n```",
            f"## Legenda\n{result.legend}",
        ]
        return "\n\n".join(lines)

    # Fallback genérico para qualquer outro Pydantic model
    try:
        data = result.model_dump()
        return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"
    except Exception:
        return str(result)


# ─── Funções de geração ──────────────────────────────────────────────────────

def _get_generator_fn(content_type_key: str):
    """Importa dinamicamente a função de geração correta."""
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


def generate_content(student_name: str, topic: str, content_type_key: str, version: str) -> str:
    """Chama o generator e retorna Markdown formatado."""
    if not topic or not topic.strip():
        return "_Por favor, insira um tópico._"

    profile = PROFILE_MAP.get(student_name)
    if not profile:
        return "_Aluno não encontrado._"

    try:
        fn = _get_generator_fn(content_type_key)
        result = fn(profile=profile, topic=topic.strip(), version=version)
        return _format_result(result)
    except Exception as exc:
        return f"**Erro ao gerar conteúdo.**\n\n`{exc}`\n\n_Verifique se a variável `GEMINI_API_KEY` está configurada corretamente._"


def generate_both_versions(
    student_name: str, topic: str, content_type_key: str
) -> tuple[str, str]:
    """Dispara v1 e v2 em paralelo e retorna (output_v1, output_v2)."""
    if not topic or not topic.strip():
        return "_Por favor, insira um tópico._", "_Por favor, insira um tópico._"

    profile = PROFILE_MAP.get(student_name)
    if not profile:
        return "_Aluno não encontrado._", "_Aluno não encontrado._"

    def _call(ver: str) -> str:
        try:
            fn = _get_generator_fn(content_type_key)
            result = fn(profile=profile, topic=topic.strip(), version=ver)
            return _format_result(result)
        except Exception as exc:
            return f"**Erro ({ver}).**\n\n`{exc}`"

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fut_v1 = pool.submit(_call, "v1")
        fut_v2 = pool.submit(_call, "v2")
        out_v1 = fut_v1.result()
        out_v2 = fut_v2.result()

    return out_v1, out_v2


# ─── HTML helpers ─────────────────────────────────────────────────────────────

def _student_chips_html(student_name: str) -> str:
    """Gera HTML com chips de info do aluno selecionado."""
    profile = PROFILE_MAP.get(student_name)
    if not profile:
        return ""

    nivel = profile.get("nivel", "")
    badge_cls = NIVEL_BADGE_CLASS.get(nivel, "")
    interesses = ", ".join(profile.get("interesses", []))
    centro = profile.get("centro", "")
    curso = profile.get("curso", "")

    centro_chip = f'<span class="chip">🏛️ {centro}</span>' if centro else ""
    curso_chip  = f'<span class="chip">📚 {curso}</span>' if curso else ""

    return f"""
<div class="profile-chips">
  {centro_chip}
  {curso_chip}
  <span class="chip">{profile.get('idade', '?')} anos</span>
  <span class="chip {badge_cls} badge">{nivel}</span>
  <span class="chip">🧠 {profile.get('estilo_aprendizado', '—')}</span>
  <span class="chip">✨ {interesses}</span>
</div>
"""

# ─── Build Interface ──────────────────────────────────────────────────────────

def build_interface() -> gr.Blocks:
    student_names = list(PROFILE_MAP.keys())
    content_type_choices = list(CONTENT_TYPES.keys())

    with gr.Blocks(css=CSS, title="Prisma — Plataforma Educativa") as demo:

        # ── Header ──────────────────────────────────────────────────────────
        gr.HTML(
            value="""
<div class="prisma-header">
  <div class="prisma-eyebrow">Plataforma Educativa · UFPE</div>
  <h1 class="prisma-title"><span>Prisma</span> — Conteúdo Personalizado com IA</h1>
  <p class="prisma-subtitle">Explicações adaptadas ao perfil de cada aluno via Google Gemini</p>
</div>""",
            container=False,
        )

        with gr.Tabs():

            # ── Aba 1: Gerador ───────────────────────────────────────────────
            with gr.TabItem("📝 Gerador"):
                with gr.Row():
                    # Coluna esquerda — controles
                    with gr.Column(scale=1, min_width=260):
                        dd_student = gr.Dropdown(
                            choices=student_names,
                            value=student_names[0] if student_names else None,
                            label="👤 Aluno",
                            interactive=True,
                        )
                        chips_html = gr.HTML(
                            value=_student_chips_html(student_names[0]) if student_names else "",
                            container=False,
                        )
                        txt_topic = gr.Textbox(
                            label="📌 Tópico",
                            placeholder="ex.: fotossíntese, frações, Segunda Guerra…",
                            lines=2,
                        )
                        dd_content = gr.Dropdown(
                            choices=content_type_choices,
                            value=content_type_choices[0],
                            label="📦 Tipo de conteúdo",
                            interactive=True,
                        )
                        dd_version = gr.Dropdown(
                            choices=[
                                ("🎯 Personalizado"),
                                ("📝 Direto"),
                            ],
                            value="v2",
                            label="🔖 Estilo do prompt",
                            interactive=True,
                        )
                        btn_generate = gr.Button(
                            "Gerar Conteúdo →",
                            variant="primary",
                            size="lg",
                        )

                    # Coluna direita — output
                    with gr.Column(scale=2):
                        md_output = gr.Markdown(
                            value="_Preencha os campos e clique em **Gerar Conteúdo →**_",
                            label="📄 Resultado",
                        )

                # Eventos — Aba Gerador
                dd_student.change(
                    fn=_student_chips_html,
                    inputs=[dd_student],
                    outputs=[chips_html],
                )
                btn_generate.click(
                    fn=generate_content,
                    inputs=[dd_student, txt_topic, dd_content, dd_version],
                    outputs=[md_output],
                )

            # ── Aba 2: Comparar Prompts ───────────────────────────────────────
            with gr.TabItem("⚖️ Comparar Prompts"):
                with gr.Row():
                    dd_cmp_student = gr.Dropdown(
                        choices=student_names,
                        value=student_names[0] if student_names else None,
                        label="👤 Aluno",
                        interactive=True,
                    )
                    txt_cmp_topic = gr.Textbox(
                        label="📌 Tópico",
                        placeholder="ex.: derivadas, fotossíntese…",
                        lines=1,
                    )
                    dd_cmp_content = gr.Dropdown(
                        choices=content_type_choices,
                        value=content_type_choices[0],
                        label="📦 Tipo de conteúdo",
                        interactive=True,
                    )

                btn_compare = gr.Button(
                    "Comparar: Direto vs Personalizado →",
                    variant="primary",
                    size="lg",
                )

                with gr.Row():
                    md_v1 = gr.Markdown(
                        value="_Aguardando comparação…_",
                        label="� Prompt Direto — sem contexto do aluno",
                    )
                    md_v2 = gr.Markdown(
                        value="_Aguardando comparação…_",
                        label="🎯 Prompt Personalizado — perfil + chain-of-thought",
                    )

                # Evento — Aba Comparar
                btn_compare.click(
                    fn=generate_both_versions,
                    inputs=[dd_cmp_student, txt_cmp_topic, dd_cmp_content],
                    outputs=[md_v1, md_v2],
                )


        # ── Footer ──────────────────────────────────────────────────────────
        gr.HTML(
            value='<div class="prisma-footer">Prisma · Plataforma Educativa com IA · Powered by Google Gemini</div>',
            container=False,
        )

    return demo


# ─── Standalone ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    demo = build_interface()
    demo.launch()
