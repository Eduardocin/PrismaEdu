"""
gemini_client.py
Wrapper da API Google Gemini com tratamento de erros.
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GEMINI_API_KEY")
_model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if not _api_key:
    raise EnvironmentError("GEMINI_API_KEY não encontrada. Verifique o arquivo .env")

_client = genai.Client(api_key=_api_key)


def generate(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.7,
    response_schema=None,
    max_output_tokens: int | None = None,
) -> str:
    """
    Envia um prompt ao Gemini e retorna o texto gerado.

    Args:
        prompt: Texto do prompt do usuário.
        system_instruction: Instrução de sistema (persona + regras).
        temperature: Criatividade da resposta (0.0 = determinístico, 1.0 = criativo).
        response_schema: Modelo Pydantic opcional. Quando fornecido, força resposta
                         em JSON estruturado e validado (Output Schema).
        max_output_tokens: Limite de tokens no output. None = sem limite explícito.

    Returns:
        Texto gerado (JSON string quando response_schema for informado).

    Raises:
        ValueError: Se o prompt estiver vazio.
        RuntimeError: Se a API retornar erro.
    """
    if not prompt or not prompt.strip():
        raise ValueError("O prompt não pode ser vazio.")

    try:
        config_kwargs = {
            "temperature": temperature,
            "system_instruction": system_instruction or None,
        }

        if max_output_tokens is not None:
            config_kwargs["max_output_tokens"] = max_output_tokens

        if response_schema is not None:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_kwargs)

        response = _client.models.generate_content(
            model=_model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    except Exception as e:
        raise RuntimeError(f"Erro ao chamar a API Gemini: {e}") from e


if __name__ == "__main__":
    print(f"Modelo: {_model_name}")
    print("Enviando prompt de teste...\n")

    resposta = generate(
        prompt="Explique o conceito de fotossíntese em uma frase simples.",
        system_instruction="Você é um professor didático e objetivo.",
        temperature=0.5,
    )
    print("Resposta:")
    print(resposta)
