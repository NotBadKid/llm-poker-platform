import requests
import json
import config
import time
import random


MAX_RETRIES = 3
INITIAL_BACKOFF = 2

schema_prompt="You are a professional poker player. Analyze the provided game state and return your decision as a valid JSON object. Do not include any other text, reasoning, or explanations outside of the JSON object. The JSON object must strictly follow this format: {\"action\": \"your_action\", \"amount\": your_amount, \"message\": \"your_comment\"}. The message field is public table talk. Every opponent sees it. You may or may not use this to your advantage. Remember that other players also may bluff. In your game please follow that strategy:"

text_schema_prompt = """You are a professional poker player. Analyze the provided game state and return your decision in a strict text format.
Do not wrap the output in markdown code blocks. Do not add explanations.
Use exactly this format:

action: [your_action]
amount: [your_amount]
message: [your_comment]

Valid actions are: fold, check, call, bet, raise, all_in.
The message is public table talk.
In your game please follow that strategy:"""

default_prompt = "play optimally , based on your hand , position and pot odds, play GTO"
def get_llm_action(model_id: str, prompt_json: dict, user_prompt:str = default_prompt, temperature:float = 1.0) -> dict | None:
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
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": schema_prompt+user_prompt
            },
            {
                "role": "user",
                "content": prompt_content
            }
        ]
    }

    print(f"[LLM Manager] Sending prompt to model: {model_id}...")

    for attempt in range(MAX_RETRIES+1):
        print(f"[LLM Manager] Attempt {attempt + 1} of {MAX_RETRIES + 1}...")
        try:
            response = requests.post(
                config.OPENROUTER_API_URL,
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )

            if response.status_code == 429:
                if attempt < MAX_RETRIES:
                    sleep_time = INITIAL_BACKOFF * (2 ** attempt) + random.uniform(0, 1)
                    print(
                        f"[LLM Manager] Rate Limit (429). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    print(f"[LLM Manager] Error: 429 Rate Limit exceeded after {MAX_RETRIES} retries.")
                    return None

            if response.status_code == 400:
                print(f"[LLM Manager] Error 400 (Bad Request). Response body: {response.text}")
                return None

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
            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue
            return None
        except KeyError:
            print(f"[LLM Manager] Error: Unexpected response format from OpenRouter.")
            print(f"Received: {response.text}")
            return None


def get_llm_action_text(model_id: str, prompt_json: dict, user_prompt: str = default_prompt,
                        temperature: float = 1.0) -> dict | None:
    """
    NEW FUNCTION: Sends prompt expecting Simple Text response (key:value).
    Parses the text back into a dictionary compatible with the poker engine.
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
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": text_schema_prompt + user_prompt
            },
            {
                "role": "user",
                "content": prompt_content
            }
        ]
    }

    print(f"[LLM Manager TEXT] Sending prompt to model: {model_id}...")

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(
                config.OPENROUTER_API_URL,
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )

            if response.status_code == 429:
                if attempt < MAX_RETRIES:
                    sleep_time = INITIAL_BACKOFF * (2 ** attempt) + random.uniform(0, 1)
                    print(f"[LLM Manager] Rate Limit (429). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    print(f"[LLM Manager] Error: 429 Rate Limit exceeded.")
                    return None

            if response.status_code == 400:
                print(f"[LLM Manager] Error 400 (Bad Request). Response body: {response.text}")
                return None

            response.raise_for_status()
            response_data = response.json()

            raw_content = response_data['choices'][0]['message']['content']
            print(f"[LLM Manager] Received RAW text response:\n{raw_content}")

            parsed_action = parse_text_response(raw_content)

            if parsed_action:
                print(f"[LLM Manager] Parsed to: {parsed_action}")
                return parsed_action
            else:
                print(f"[LLM Manager] Error: Could not parse text response.")
                return None

        except requests.exceptions.RequestException as e:
            print(f"[LLM Manager] API error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue
            return None
        except KeyError:
            print(f"[LLM Manager] Error: Unexpected response structure.")
            return None

    return None


def parse_text_response(text: str) -> dict | None:
    """
    Parses a string like:
    action: fold
    amount: 0
    message: some text

    Into: {"action": "fold", "amount": 0, "message": "some text"}
    """
    try:
        result = {
            "action": "fold",
            "amount": 0,
            "message": ""
        }

        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line: continue

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if key == 'action':
                    clean_action = value.replace('"', '').replace("'", "").replace('.', '').lower()
                    result['action'] = clean_action

                elif key == 'amount':
                    try:
                        clean_amount = ''.join(c for c in value if c.isdigit() or c == '.')
                        if clean_amount:
                            result['amount'] = float(clean_amount)
                    except ValueError:
                        result['amount'] = 0

                elif key == 'message':
                    result['message'] = value.replace('"', '')

        return result

    except Exception as e:
        print(f"[LLM Manager] Parsing exception: {e}")
        return None