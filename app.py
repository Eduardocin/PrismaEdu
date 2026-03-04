"""
app.py
Entry point para deploy no Hugging Face Spaces.

No HF Spaces, o GEMINI_API_KEY deve ser configurado como Secret
nas configurações do Space (Settings → Variables and secrets).
A variável é injetada automaticamente como variável de ambiente —
o load_dotenv() em gemini_client.py é ignorado sem erro quando
não há arquivo .env, e os os.getenv() funcionam normalmente.
"""

from app.interface import build_interface

demo = build_interface()

if __name__ == "__main__":
    demo.launch()
