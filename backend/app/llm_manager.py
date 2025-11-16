import requests
import json
import config


def get_llm_action(model_id: str, prompt_json: dict) -> dict | None:
    """
    Wysyła prompt do określonego modelu LLM przez OpenRouter i zwraca
    sparsowaną odpowiedź JSON.

    Args:
        model_id (str): Nazwa modelu na OpenRouter (np. "openai/gpt-4o")
        prompt_json (dict): Cały obiekt JSON, który ma być wysłany.

    Returns:
        dict | None: Słownik z akcją (np. {"action": "bet", ...}) lub
                     None w przypadku błędu.
    """

    prompt_content = json.dumps(prompt_json)

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": config.APP_URL_REFERER,
        "X-Title": config.APP_TITLE
    }

    data = {
        "model": model_id,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are a professional poker player. Analyze the provided game state and return your decision as a valid JSON object. Do not include any other text, reasoning, or explanations outside of the JSON object. The JSON object must strictly follow this format: {\"action\": \"your_action\", \"amount\": your_amount, \"message\": \"your_comment\"}."
            },
            {
                "role": "user",
                "content": prompt_content
            }
        ]
    }

    print(f"[LLM Manager] Wysyłanie żądania do modelu: {model_id}...")

    try:
        response = requests.post(
            config.OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=30
        )

        response.raise_for_status()

        response_data = response.json()

        print(response_data)
        llm_response_content = response_data['choices'][0]['message']['content']

        print(f"[LLM Manager] Otrzymano odpowiedź: {llm_response_content}")

        try:
            action_json = json.loads(llm_response_content)
            if "action" not in action_json:
                print(f"[LLM Manager] Błąd: 'action' brak w odpowiedzi LLM.")
                return None

            return action_json

        except json.JSONDecodeError:
            print(f"[LLM Manager] Błąd: Model LLM nie zwrócił poprawnego JSON-a.")
            print(f"Otrzymano: {llm_response_content}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[LLM Manager] Błąd API OpenRouter: {e}")
        return None
    except KeyError:
        print(f"[LLM Manager] Błąd: Nieoczekiwany format odpowiedzi od OpenRouter.")
        print(f"Otrzymano: {response.text}")
        return None