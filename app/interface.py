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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; }

body, .gradio-container {
    font-family: 'DM Sans', sans-serif !important;
    background: #F7F7F5 !important;
    color: #1A1A1A !important;
}

/* ── Header ── */
.prisma-header {
    text-align: center;
    padding: 2rem 1rem 1.5rem;
    border-bottom: 1px solid #E4E4E0;
    margin-bottom: 1.5rem;
}
.prisma-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 0.4rem;
}
.prisma-title {
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #1A1A1A;
    margin: 0 0 0.4rem;
}
.prisma-title span { color: #2D6BE4; }
.prisma-subtitle {
    font-size: 0.95rem;
    color: #666;
    font-weight: 400;
}

/* ── Tabs ── */
.tab-nav button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    color: #888 !important;
    background: transparent !important;
    padding: 0.6rem 1.2rem !important;
}
.tab-nav button.selected {
    color: #2D6BE4 !important;
    border-bottom-color: #2D6BE4 !important;
}

/* ── Inputs ── */
.gradio-container input,
.gradio-container textarea,
.gradio-container .wrap-inner,
.gradio-container select {
    font-family: 'DM Sans', sans-serif !important;
    background: #FFFFFF !important;
    color: #1A1A1A !important;
    border: 1px solid #DDDDD8 !important;
    border-radius: 8px !important;
}

/* ── Labels visíveis ── */
.gradio-container label > span,
.gradio-container .label-wrap span {
    color: #444444 !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Tabs — texto visível ── */
.tab-nav button span,
.tab-nav button {
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: unset !important;
}

/* ── Output markdown — texto escuro ── */
.gradio-container .prose,
.gradio-container .prose p,
.gradio-container .prose li,
.gradio-container .prose h1,
.gradio-container .prose h2,
.gradio-container .prose h3 {
    color: #1A1A1A !important;
}

/* ── Botão primário ── */
.btn-primary {
    background: #1A1A1A !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.4rem !important;
    cursor: pointer !important;
    transition: opacity 0.15s ease !important;
    width: 100% !important;
}
.btn-primary:hover { opacity: 0.8 !important; }

/* ── Chips de perfil ── */
.profile-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 10px 0 4px;
}
.chip {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid #E4E4E0;
    background: #fff;
    color: #555;
    white-space: nowrap;
}
.chip-level-iniciante    { background: #D4EDDA; border-color: #B8DACC; color: #276133; }
.chip-level-intermediário { background: #FFF3CD; border-color: #F5E07F; color: #856404; }
.chip-level-avancado     { background: #CCE5FF; border-color: #99C9FF; color: #0C5299; }

/* ── Cards de perfil ── */
.profiles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
    padding: 1rem 0;
}
.profile-card {
    background: #fff;
    border: 1px solid #E4E4E0;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    font-family: 'DM Sans', sans-serif;
}
.profile-card-name {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.6rem;
    color: #1A1A1A;
}
.profile-card-meta {
    font-size: 0.82rem;
    color: #666;
    margin-bottom: 0.8rem;
    line-height: 1.6;
}
.profile-card-desc {
    font-size: 0.82rem;
    color: #888;
    line-height: 1.5;
    border-top: 1px solid #F0F0EC;
    padding-top: 0.7rem;
    margin-top: 0.4rem;
}
.badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 500;
}
.badge-iniciante    { background: #D4EDDA; color: #276133; }
.badge-intermediário { background: #FFF3CD; color: #856404; }
.badge-avançado     { background: #CCE5FF; color: #0C5299; }

/* ── Output markdown ── */
.output-box {
    background: #fff;
    border: 1px solid #E4E4E0;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    min-height: 200px;
}

/* ── Compare columns ── */
.compare-col-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #888;
    margin-bottom: 0.4rem;
}

/* ── Footer ── */
.prisma-footer {
    text-align: center;
    padding: 1.5rem 1rem;
    margin-top: 2rem;
    border-top: 1px solid #E4E4E0;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    color: #aaa;
}
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


def _profiles_cards_html() -> str:
    """Gera grid de cards HTML para todos os alunos."""
    cards = []
    for p in PROFILES:
        nivel = p.get("nivel", "")
        badge_cls = NIVEL_BADGE_CLASS.get(nivel, "")
        interesses = ", ".join(p.get("interesses", []))
        centro = p.get("centro", "")
        curso  = p.get("curso", "")
        centro_tag = f'<span class="badge" style="background:#EEF2FF;color:#3730A3;">{centro}</span>&nbsp;' if centro else ""
        card = f"""
<div class="profile-card">
  <div class="profile-card-name">{p.get('nome', '—')}</div>
  <div class="profile-card-meta">
    {centro_tag}<span class="badge {badge_cls}">{nivel}</span>&nbsp;&nbsp;
    {p.get('idade', '?')} anos · <strong>{curso}</strong><br>
    estilo: <strong>{p.get('estilo_aprendizado', '—')}</strong>&nbsp;·
    <span style="color:#aaa;">interesses:</span> {interesses}
  </div>
  <div class="profile-card-desc">{p.get('descricao', '')}</div>
</div>
"""
        cards.append(card)
    return '<div class="profiles-grid">' + "".join(cards) + "</div>"


# ─── Build Interface ──────────────────────────────────────────────────────────

def build_interface() -> gr.Blocks:
    student_names = list(PROFILE_MAP.keys())
    content_type_choices = list(CONTENT_TYPES.keys())

    with gr.Blocks(css=CSS, title="Prisma — Plataforma Educativa", theme=gr.themes.Base()) as demo:

        # ── Header ──────────────────────────────────────────────────────────
        gr.HTML("""
<div class="prisma-header">
  <div class="prisma-eyebrow">Plataforma Educativa</div>
  <h1 class="prisma-title"><span>Prisma</span> — Conteúdo Personalizado com IA</h1>
  <p class="prisma-subtitle">
    Gera explicações adaptadas ao perfil, nível e estilo de aprendizado de cada aluno
    usando o <strong>Google Gemini</strong>.
  </p>
</div>
""")

        with gr.Tabs():

            # ── Aba 1: Gerador ───────────────────────────────────────────────
            with gr.TabItem("📝 Gerador"):
                with gr.Row():
                    # Coluna esquerda — controles
                    with gr.Column(scale=1):
                        dd_student = gr.Dropdown(
                            choices=student_names,
                            value=student_names[0] if student_names else None,
                            label="Aluno",
                            interactive=True,
                        )
                        chips_html = gr.HTML(
                            value=_student_chips_html(student_names[0]) if student_names else "",
                        )
                        txt_topic = gr.Textbox(
                            label="Tópico",
                            placeholder="ex.: fotossíntese, frações, Segunda Guerra Mundial…",
                            lines=2,
                        )
                        dd_content = gr.Dropdown(
                            choices=content_type_choices,
                            value=content_type_choices[0],
                            label="Tipo de conteúdo",
                            interactive=True,
                        )
                        dd_version = gr.Dropdown(
                            choices=["v2", "v1"],
                            value="v2",
                            label="Versão do prompt",
                            interactive=True,
                        )
                        btn_generate = gr.Button(
                            "Gerar Conteúdo →",
                            elem_classes=["btn-primary"],
                        )

                    # Coluna direita — output
                    with gr.Column(scale=2):
                        md_output = gr.Markdown(
                            value="_Preencha os campos e clique em **Gerar Conteúdo →**_",
                            elem_classes=["output-box"],
                            label="Resultado",
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
                        label="Aluno",
                        interactive=True,
                    )
                    txt_cmp_topic = gr.Textbox(
                        label="Tópico",
                        placeholder="ex.: derivadas, fotossíntese…",
                        lines=1,
                    )
                    dd_cmp_content = gr.Dropdown(
                        choices=content_type_choices,
                        value=content_type_choices[0],
                        label="Tipo de conteúdo",
                        interactive=True,
                    )

                btn_compare = gr.Button(
                    "Comparar v1 vs v2 →",
                    elem_classes=["btn-primary"],
                )

                with gr.Row():
                    with gr.Column():
                        gr.HTML('<div class="compare-col-label">Prompt v1 — simples</div>')
                        md_v1 = gr.Markdown(
                            value="_Aguardando comparação…_",
                            elem_classes=["output-box"],
                            label="v1",
                        )
                    with gr.Column():
                        gr.HTML('<div class="compare-col-label">Prompt v2 — estruturado</div>')
                        md_v2 = gr.Markdown(
                            value="_Aguardando comparação…_",
                            elem_classes=["output-box"],
                            label="v2",
                        )

                # Evento — Aba Comparar
                btn_compare.click(
                    fn=generate_both_versions,
                    inputs=[dd_cmp_student, txt_cmp_topic, dd_cmp_content],
                    outputs=[md_v1, md_v2],
                )

            # ── Aba 3: Perfis ─────────────────────────────────────────────────
            with gr.TabItem("👥 Perfis"):
                gr.HTML(_profiles_cards_html())

        # ── Footer ──────────────────────────────────────────────────────────
        gr.HTML("""
<div class="prisma-footer">
  Prisma · Plataforma Educativa com IA · Powered by Google Gemini
</div>
""")

    return demo


# ─── Standalone ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    demo = build_interface()
    demo.launch()
