
class ScenarioDto:
    def __init__(self, small_blid, big_blind, players, default_prompts, default_temperature, starting_stack):
        self.small_blind = small_blid
        self.big_blind = big_blind
        self.players = players
        self.default_prompts = default_prompts
        self.default_temperature = default_temperature
        self.starting_stack = starting_stack  # Corrected: Added assignment for starting_stack


# Define the constants for the default scenario
DEFAULT_SB = 100
DEFAULT_BB = 200
DEFAULT_PLAYERS = 4
# Assuming these are boolean flags or non-empty values for the default
DEFAULT_PROMPTS =""
DEFAULT_TEMPERATURE = 1
DEFAULT_STACK = 10000


def verify_if_scenario_matches_default(input_scenario: ScenarioDto):
    """
    Checks if the input_scenario matches the predefined default scenario.
    Returns True if a match, or a dictionary of differences otherwise.
    """
    # 1. Define the default scenario's expected values
    default_scenario = {
        'small_blind': DEFAULT_SB,
        'big_blind': DEFAULT_BB,
        'players': DEFAULT_PLAYERS,
        'default_prompts': DEFAULT_PROMPTS,
        'default_temperature': DEFAULT_TEMPERATURE,
        'starting_stack': DEFAULT_STACK,
    }

    # 2. Get the input scenario's actual values (assuming they exist)
    input_values = {
        'small_blind': input_scenario.small_blind,
        'big_blind': input_scenario.big_blind,
        'players': input_scenario.players,
        'default_prompts': input_scenario.default_prompts,
        'default_temperature': input_scenario.default_temperature,
        'starting_stack': input_scenario.starting_stack,
    }

    # 3. Compare the two scenarios and collect differences
    differences = {}

    for key, default_value in default_scenario.items():
        # Get the actual value from the input_values dictionary
        actual_value = input_values.get(key)

        # Check for difference
        if actual_value != default_value:
            differences[key] = {
                'Expected': default_value,
                'Actual': actual_value
            }

    # 4. Return the result
    if not differences:
        return True
    else:
        return differences


def map_game_config_to_scenario(game_config: dict) -> ScenarioDto:
    """
    Maps a game configuration dictionary to a ScenarioDto instance,
    ensuring maximum safety against missing keys (KeyError) and explicit
    None values for required parameters.
    """

    # Helper to get value, checking for key presence AND if the value is None
    def get_safe_value(key, default):
        value = game_config.get(key, default)
        return default if value is None else value

    sb = get_safe_value('small_blind', DEFAULT_SB)
    bb = get_safe_value('big_blind', DEFAULT_BB)

    # 1. Handle Players Count Robustly
    players_data = game_config.get('players')
    if isinstance(players_data, list):
        players_count = len(players_data)
    else:
        # If key is missing, None, or not a list, use the default count
        players_count = DEFAULT_PLAYERS

    # 2. Handle boolean/numeric flags
    prompts = get_safe_value('use_default_prompts', DEFAULT_PROMPTS)
    temp = get_safe_value('use_default_temperature', DEFAULT_TEMPERATURE)
    stack = get_safe_value('initial_stack', DEFAULT_STACK)

    scenario_dto = ScenarioDto(
        small_blid=sb,
        big_blind=bb,
        players=players_count,
        default_prompts=prompts,
        default_temperature=temp,
        starting_stack=stack
    )

    return scenario_dto
