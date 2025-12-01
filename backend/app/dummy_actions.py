import random


def get_dummy_action(model_id: str, prompt_json: dict) -> dict | None:
    """
    Mock function that simulates LLM behavior for testing.
    Returns a Python Dictionary directly, matching the signature of get_llm_action.
    """
    actions = ["fold", "bet", "raise", "check"]

    selected_action = random.choice(actions)

    if selected_action in ["fold", "check"]:
        amount = 0
    else:
        amount = random.randint(10, 100)  # Bet/Raise zazwyczaj > 0

    response_data = {
        "action": selected_action,
        "amount": amount,
        "message": f"Dummy action: {selected_action} (simulated)"
    }

    print(f"[Dummy Manager] Returning simulated action: {response_data}")

    return response_data