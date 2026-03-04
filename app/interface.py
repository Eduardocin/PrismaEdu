"""
interface.py
Interface Gradio do Prisma â€” Plataforma Educativa com IA.

Uso standalone: python app/interface.py
"""

import json
import concurrent.futures
from pathlib import Path

import gradio as gr

# â”€â”€â”€ CSS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CSS = """
/* â”€â”€ Header â”€â”€ */
.prisma-header { text-align: center; padding: 1.2rem 1rem 0.8rem; margin-bottom: 0.5rem; }
.prisma-eyebrow { font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; opacity: 0.5; }
.prisma-title { font-size: 1.7rem; font-weight: 700; margin: 0.2rem 0; }
.prisma-title span { color: #2D6BE4; }
.prisma-subtitle { font-size: 0.88rem; opacity: 0.6; }

/* â”€â”€ Chips de perfil â”€â”€ */
.profile-chips { display: flex; flex-wrap: wrap; gap: 5px; padding: 6px 0; }
.chip { font-size: 0.71rem; padding: 2px 9px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.15); white-space: nowrap; }
.badge-iniciante    { color: #276133; background: #D4EDDA; border-color: #B8DACC; }
.badge-intermediÃ¡rio { color: #856404; background: #FFF3CD; border-color: #F5E07F; }
.badge-avanÃ§ado     { color: #0C5299; background: #CCE5FF; border-color: #99C9FF; }

/* â”€â”€ Footer â”€â”€ */
.prisma-footer { text-align: center; padding: 0.8rem; margin-top: 1rem; font-size: 0.7rem; opacity: 0.4; }
"""

# â”€â”€â”€ Constantes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CONTENT_TYPES: dict[str, str] = {
    "ðŸ’¡ ExplicaÃ§Ã£o Conceitual": "conceptual",
    "ðŸ”¬ Exemplos PrÃ¡ticos":     "examples",
    "ðŸ¤” Perguntas de ReflexÃ£o": "reflection",
    "ðŸ—ºï¸ Resumo Visual":         "visual",
}

NIVEL_BADGE_CLASS: dict[str, str] = {
    "iniciante":    "badge-iniciante",
    "intermediÃ¡rio": "badge-intermediÃ¡rio",
    "avanÃ§ado":     "badge-avanÃ§ado",
}

NIVEIS      = ["iniciante", "intermediÃ¡rio", "avanÃ§ado"]
ESTILOS     = ["visual", "auditivo", "leitura-escrita", "cinestÃ©sico"]

# â”€â”€â”€ Montagem de perfil a partir de campos do formulÃ¡rio â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _build_profile(nome: str, idade: int | str, centro: str, nivel: str,
                   estilo: str, interesses_raw: str) -> dict:
    """ConstrÃ³i o dict de perfil a partir dos campos livres digitados pelo usuÃ¡rio."""
    interesses = [i.strip() for i in interesses_raw.split(",") if i.strip()]
    return {
        "id": f"user_{nome.lower().replace(' ', '_')}",
        "nome": nome.strip(),
        "idade": int(idade) if str(idade).strip().isdigit() else 0,
        "centro": centro.strip(),
        "nivel": nivel,
        "estilo_aprendizado": estilo,
        "interesses": interesses,
        "descricao": "",
    }

# â”€â”€â”€ FormataÃ§Ã£o de resultado â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _format_result(result: object) -> str:
    """Converte qualquer resultado de generator para Markdown legÃ­vel."""
    if result is None:
        return "_Nenhum conteÃºdo gerado._"

    # v1: dict com chave 'raw'
    if isinstance(result, dict):
        return result.get("raw", str(result))

    # Pydantic model â€” verificar tipo pelo nome da classe
    cls_name = type(result).__name__

    if cls_name == "ConceptualResponse":
        lines = [
            f"## DefiniÃ§Ã£o\n{result.definition}",
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
            f"## VariaÃ§Ã£o / ExercÃ­cio\n{result.variation}",
        ]
        return "\n\n".join(lines)

    if cls_name == "ReflectionResponse":
        qs = "\n".join(f"{i+1}. {q}" for i, q in enumerate(result.questions))
        return f"## Perguntas de ReflexÃ£o\n\n{qs}"

    if cls_name == "VisualResponse":
        lines = [
            f"## Analogia\n{result.analogy}",
            f"## RepresentaÃ§Ã£o Visual\n```\n{result.visual_representation}\n```",
            f"## Legenda\n{result.legend}",
        ]
        return "\n\n".join(lines)

    # Fallback genÃ©rico para qualquer outro Pydantic model
    try:
        data = result.model_dump()
        return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"
    except Exception:
        return str(result)


# â”€â”€â”€ FunÃ§Ãµes de geraÃ§Ã£o â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _get_generator_fn(content_type_key: str):
    """Importa dinamicamente a funÃ§Ã£o de geraÃ§Ã£o correta."""
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
    nome: str, idade, centro: str, nivel: str, estilo: str, interesses_raw: str,
    topic: str, content_type_key: str, version: str,
) -> str:
    """Chama o generator com o perfil montado a partir dos campos do formulÃ¡rio."""
    if not nome or not nome.strip():
        return "_Por favor, preencha o nome do aluno._"
    if not topic or not topic.strip():
        return "_Por favor, insira um tÃ³pico._"

    profile = _build_profile(nome, idade, centro, nivel, estilo, interesses_raw)

    try:
        fn = _get_generator_fn(content_type_key)
        result = fn(profile=profile, topic=topic.strip(), version=version)
        return _format_result(result)
    except Exception as exc:
        return (
            f"**Erro ao gerar conteÃºdo.**\n\n`{exc}`\n\n"
            "_Verifique se a variÃ¡vel `GEMINI_API_KEY` estÃ¡ configurada._"
        )


def generate_both_versions(
    nome: str, idade, centro: str, nivel: str, estilo: str, interesses_raw: str,
    topic: str, content_type_key: str,
) -> tuple[str, str]:
    """Dispara v1 e v2 em paralelo e retorna (output_v1, output_v2)."""
    if not nome or not nome.strip():
        return "_Por favor, preencha o nome do aluno._", "_Por favor, preencha o nome do aluno._"
    if not topic or not topic.strip():
        return "_Por favor, insira um tÃ³pico._", "_Por favor, insira um tÃ³pico._"

    profile = _build_profile(nome, idade, centro, nivel, estilo, interesses_raw)

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


# â”€â”€â”€ HTML helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _student_chips_html(nome: str, idade, centro: str, nivel: str,
                        estilo: str, interesses_raw: str) -> str:
    """Gera HTML com chips de resumo do perfil digitado."""
    if not nome or not nome.strip():
        return ""
    badge_cls = NIVEL_BADGE_CLASS.get(nivel, "")
    interesses = ", ".join(i.strip() for i in interesses_raw.split(",") if i.strip())
    centro_chip = f'<span class="chip">ðŸ›ï¸ {centro}</span>' if centro.strip() else ""
    return f"""
<div class="profile-chips">
  {centro_chip}
  <span class="chip">{idade} anos</span>
  <span class="chip {badge_cls} badge">{nivel}</span>
  <span class="chip">ðŸ§  {estilo}</span>
  <span class="chip">âœ¨ {interesses}</span>
</div>
"""

# â”€â”€â”€ Build Interface â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _student_form(prefix: str = "") -> tuple:
    """
    Cria e retorna os campos do formulÃ¡rio de perfil do aluno.
    Retorna uma tupla com todos os componentes Gradio para serem usados
    em inputs/outputs de eventos.
    """
    txt_nome = gr.Textbox(
        label="ðŸ‘¤ Nome do aluno",
        placeholder="ex.: Ana Beatriz",
    )
    num_idade = gr.Number(
        label="ðŸŽ‚ Idade",
        value=18,
        minimum=1,
        maximum=99,
        precision=0,
    )
    txt_centro = gr.Textbox(
        label="ðŸ›ï¸ Centro / Unidade",
        placeholder="ex.: CIn, CCSA, CTGâ€¦",
    )
    dd_nivel = gr.Dropdown(
        choices=NIVEIS,
        value="intermediÃ¡rio",
        label="ðŸ“Š NÃ­vel",
        interactive=True,
    )
    dd_estilo = gr.Dropdown(
        choices=ESTILOS,
        value="visual",
        label="ðŸ§  Estilo de aprendizado",
        interactive=True,
    )
    txt_interesses = gr.Textbox(
        label="âœ¨ Interesses (separados por vÃ­rgula)",
        placeholder="ex.: mÃºsica, robÃ³tica, fotografia",
    )
    return txt_nome, num_idade, txt_centro, dd_nivel, dd_estilo, txt_interesses


def build_interface() -> gr.Blocks:
    content_type_choices = list(CONTENT_TYPES.keys())

    with gr.Blocks(css=CSS, title="Prisma â€” Plataforma Educativa") as demo:

        # â”€â”€ Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        gr.HTML(
            value="""
<div class="prisma-header">
  <div class="prisma-eyebrow">Plataforma Educativa Â· UFPE</div>
  <h1 class="prisma-title"><span>Prisma</span> â€” ConteÃºdo Personalizado com IA</h1>
  <p class="prisma-subtitle">ExplicaÃ§Ãµes adaptadas ao perfil de cada aluno via Google Gemini</p>
</div>""",
            container=False,
        )

        with gr.Tabs():

            # â”€â”€ Aba 1: Gerador â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            with gr.TabItem("ðŸ“ Gerador"):
                with gr.Row():
                    # Coluna esquerda â€” controles
                    with gr.Column(scale=1, min_width=280):
                        gr.Markdown("### Perfil do aluno")
                        txt_nome, num_idade, txt_centro, dd_nivel, dd_estilo, txt_interesses = _student_form()
                        chips_html = gr.HTML(container=False)

                        gr.Markdown("### ConteÃºdo")
                        txt_topic = gr.Textbox(
                            label="ðŸ“Œ TÃ³pico",
                            placeholder="ex.: fotossÃ­ntese, fraÃ§Ãµes, Segunda Guerraâ€¦",
                            lines=2,
                        )
                        dd_content = gr.Dropdown(
                            choices=content_type_choices,
                            value=content_type_choices[0],
                            label="ðŸ“¦ Tipo de conteÃºdo",
                            interactive=True,
                        )
                        dd_version = gr.Dropdown(
                            choices=["v2", "v1"],
                            value="v2",
                            label="ðŸ”– VersÃ£o do prompt  (v2 = personalizado | v1 = direto)",
                            interactive=True,
                        )
                        btn_generate = gr.Button(
                            "Gerar ConteÃºdo â†’",
                            variant="primary",
                            size="lg",
                        )

                    # Coluna direita â€” output
                    with gr.Column(scale=2):
                        md_output = gr.Markdown(
                            value="_Preencha os campos e clique em **Gerar ConteÃºdo â†’**_",
                            label="ðŸ“„ Resultado",
                        )

                _profile_inputs = [txt_nome, num_idade, txt_centro, dd_nivel, dd_estilo, txt_interesses]

                # Chips atualizam ao mudar qualquer campo de perfil
                for field in _profile_inputs:
                    field.change(
                        fn=_student_chips_html,
                        inputs=_profile_inputs,
                        outputs=[chips_html],
                    )

                btn_generate.click(
                    fn=generate_content,
                    inputs=_profile_inputs + [txt_topic, dd_content, dd_version],
                    outputs=[md_output],
                )

            # â”€â”€ Aba 2: Comparar Prompts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            with gr.TabItem("âš–ï¸ Comparar Prompts"):
                gr.Markdown("### Perfil do aluno")
                with gr.Row():
                    cmp_nome, cmp_idade, cmp_centro, cmp_nivel, cmp_estilo, cmp_interesses = _student_form()

                with gr.Row():
                    txt_cmp_topic = gr.Textbox(
                        label="ðŸ“Œ TÃ³pico",
                        placeholder="ex.: derivadas, fotossÃ­nteseâ€¦",
                        lines=1,
                    )
                    dd_cmp_content = gr.Dropdown(
                        choices=content_type_choices,
                        value=content_type_choices[0],
                        label="ðŸ“¦ Tipo de conteÃºdo",
                        interactive=True,
                    )

                btn_compare = gr.Button(
                    "Comparar: Direto (v1) vs Personalizado (v2) â†’",
                    variant="primary",
                    size="lg",
                )

                with gr.Row():
                    md_v1 = gr.Markdown(
                        value="_Aguardando comparaÃ§Ã£oâ€¦_",
                        label="ðŸ“ v1 â€” Prompt direto",
                    )
                    md_v2 = gr.Markdown(
                        value="_Aguardando comparaÃ§Ã£oâ€¦_",
                        label="ðŸŽ¯ v2 â€” Prompt personalizado + chain-of-thought",
                    )

                _cmp_profile = [cmp_nome, cmp_idade, cmp_centro, cmp_nivel, cmp_estilo, cmp_interesses]

                btn_compare.click(
                    fn=generate_both_versions,
                    inputs=_cmp_profile + [txt_cmp_topic, dd_cmp_content],
                    outputs=[md_v1, md_v2],
                )

        # â”€â”€ Footer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        gr.HTML(
            value='<div class="prisma-footer">Prisma Â· Plataforma Educativa com IA Â· Powered by Google Gemini</div>',
            container=False,
        )

    return demo


# â”€â”€â”€ Standalone â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    demo = build_interface()
    demo.launch()

