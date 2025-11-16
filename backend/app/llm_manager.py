import requests
import json
import config


def get_llm_action(model_id: str, prompt_json: dict) -> dict | None:
    """
    Sends prompt to specified by openRouter LLM model and returns parsed JSON response

    Args:
        model_id (str): Model name on openRouter (eg. "openai/gpt-4o")
        prompt_json (dict): Whole JSON object to be sent.

    Returns:
        dict | None: Dict with action (eg. {"action": "bet", ...}) or
                     None in case of error.
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

    print(f"[LLM Manager] Sending prompt to model: {model_id}...")

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

        print(f"[LLM Manager] Received response: {llm_response_content}")

        try:
            action_json = json.loads(llm_response_content)
            if "action" not in action_json:
                print(f"[LLM Manager] Error: no 'action' field in LLM response.")
                return None

            return action_json

        except json.JSONDecodeError:
            print(f"[LLM Manager] Error: LLM model did not return proper JSON format.")
            print(f"Received: {llm_response_content}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[LLM Manager] OpenRouter API error: {e}")
        return None
    except KeyError:
        print(f"[LLM Manager] Error: Unexpected response format from OpenRouter.")
        print(f"Received: {response.text}")
        return None