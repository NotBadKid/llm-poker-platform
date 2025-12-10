import unittest
from unittest.mock import patch, MagicMock
import io
import sys

# Correctly import the function to be tested and its dependencies
from app.poker.poker_engine import start_game_session
# These are imported by poker_engine, so we need to be able to reference them.
# We will mock the behavior of these functions in the tests.
from app.poker.game_data_validator import map_game_config_to_scenario, verify_if_scenario_matches_default, ScenarioDto

# --- Default values for creating test configurations ---
DEFAULT_SB = 100
DEFAULT_BB = 200
DEFAULT_STACK = 10000

class TestGameSessionValidation(unittest.TestCase):

    def setUp(self):
        """Set up test configurations before each test."""
        self.dummy_player = {'name': 'PlayerA', 'model_id': 'mock_model', 'temperature': 0.7}

        # 1. A valid game configuration that should pass validation
        # This implies default prompts and default temperature as per the mock logic
        self.valid_config = {
            'small_blind': DEFAULT_SB,
            'big_blind': DEFAULT_BB,
            'players': [self.dummy_player] * 4,  # 4 players
            'initial_stack': DEFAULT_STACK,
            'number_of_hands': 1
        }

        # 2. An invalid game configuration that should fail validation
        self.invalid_config = {
            'small_blind': 50,  # Invalid SB
            'big_blind': 200,
            'players': [self.dummy_player],  # Invalid player count
            'initial_stack': 10000,
            'number_of_hands': 1
        }

    # The patch decorators now target the modules as they are imported in 'poker_engine.py'
    @patch('app.poker.poker_engine.broadcaster', new_callable=MagicMock)
    @patch('app.poker.poker_engine.db', new_callable=MagicMock)
    @patch('app.poker.poker_engine.llm_manager', new_callable=MagicMock)
    # We also need to patch the validation functions that are called within start_game_session
    @patch('app.poker.poker_engine.verify_if_scenario_matches_default')
    @patch('app.poker.poker_engine.map_game_config_to_scenario')
    def run_test_scenario(self, mock_map_scenario, mock_verify_scenario, mock_llm_manager, mock_db, mock_broadcaster, game_config, verify_return_value):
        """
        Helper function to run a test scenario for start_game_session.
        It sets up mocks, runs the function, and returns the captured output and database mock.
        """
        # Configure the mock for the scenario verification function
        mock_verify_scenario.return_value = verify_return_value
        # The map function can return a dummy object, as its output is the input to the mocked verify function
        mock_map_scenario.return_value = ScenarioDto(None, None, None, None, None, None)

        # Mock the LLM to return a simple 'check' action to prevent complex game logic
        mock_llm_manager.get_llm_action.return_value = {'action': 'check', 'amount': 0, 'message': 'test'}

        # Redirect stdout to capture print statements
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            start_game_session(game_config)
            return mock_stdout.getvalue(), mock_db

    def test_01_valid_scenario_saves_to_database(self):
        """
        Test Case 1: If the scenario is valid (implies Default Prompts), database functions should be called.
        """
        # For a valid scenario, verify_if_scenario_matches_default returns True
        print_output, mock_db = self.run_test_scenario(
            game_config=self.valid_config,
            verify_return_value=True
        )

        # Assert that the "invalid data" message is NOT present
        self.assertNotIn("that data is not valid to be saved to database!!", print_output)

        # Assert that the core database functions were called
        mock_db.init_db.assert_called_once()
        mock_db.create_new_game.assert_called_once()
        mock_db.log_game_event.assert_called()  # May be called multiple times
        mock_db.save_hand_result.assert_called_once()

        print("\nTest 1 Passed: Valid data (Default Prompts) resulted in expected DB calls.")

    def test_02_invalid_scenario_prevents_database_operations(self):
        """
        Test Case 2: If the scenario is invalid (e.g. wrong blinds), no database functions should be called.
        """
        # For an invalid scenario, return a dictionary of differences
        mock_differences = {'small_blind': {'Expected': 100, 'Actual': 50}}
        print_output, mock_db = self.run_test_scenario(
            game_config=self.invalid_config,
            verify_return_value=mock_differences
        )

        # Assert that the "invalid data" message IS present
        self.assertIn("that data is not valid to be saved to database!!", print_output)

        # Assert that NO database functions were called
        mock_db.init_db.assert_not_called()
        mock_db.create_new_game.assert_not_called()
        mock_db.log_game_event.assert_not_called()
        mock_db.save_hand_result.assert_not_called()

        print("\nTest 2 Passed: Invalid data correctly skipped all database operations.")

    def test_03_custom_prompts_prevents_database_operations(self):
        """
        Test Case 3: If the scenario uses Custom Prompts (not default), it is invalid for DB saving.
        """
        # Simulate validation failure specifically due to prompts
        mock_differences = {'prompts': {'Expected': 'Default', 'Actual': 'Custom'}}
        
        # Use a config that we conceptually treat as having custom prompts
        custom_prompt_config = self.valid_config.copy()
        custom_prompt_config['custom_prompts'] = True

        print_output, mock_db = self.run_test_scenario(
            game_config=custom_prompt_config,
            verify_return_value=mock_differences
        )

        # Assert that the "invalid data" message IS present
        self.assertIn("that data is not valid to be saved to database!!", print_output)

        # Assert that NO database functions were called
        mock_db.init_db.assert_not_called()
        mock_db.create_new_game.assert_not_called()
        mock_db.log_game_event.assert_not_called()
        mock_db.save_hand_result.assert_not_called()

        print("\nTest 3 Passed: Custom prompts correctly skipped all database operations.")

if __name__ == '__main__':
    unittest.main()
