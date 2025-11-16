import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Nazwa naszej aplikacji, wysyłana w nagłówku "HTTP-Referer"
# Wymagane przez OpenRouter, aby mogli zidentyfikować projekt
# Można tu wpisać link do swojego GitHuba lub strony projektu
APP_URL_REFERER = "http://localhost:5000" # lub inna domena
APP_TITLE = "LLM Poker"