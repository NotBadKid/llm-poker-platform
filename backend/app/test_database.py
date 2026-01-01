import unittest
import pandas as pd
from unittest.mock import patch
from backend.app.database import get_aggregated_stats


class TestAggregatedStats(unittest.TestCase):

    def setUp(self):
        self.mock_data = {
            'model_id': ['Model_A', 'Model_B', 'Model_C'],
            'hand_number': [100, 200, 50],
            'net_change': [500, -200, 1000],
            'is_winner': [50, 20, 40]
        }
        self.df = pd.DataFrame(self.mock_data)

    @patch('backend.app.database.pd.read_sql')
    @patch('backend.app.database.db.session')
    @patch('backend.app.database.app.app_context')
    def test_sorts_by_total_profit_descending(self, mock_ctx, mock_session, mock_read_sql):
        mock_read_sql.return_value = self.df

        results = get_aggregated_stats(param='total_profit', ascending=False)

        self.assertEqual(results[0]['name'], 'Model_C')
        self.assertEqual(results[0]['total_profit'], 1000)
        self.assertEqual(results[1]['name'], 'Model_A')
        self.assertEqual(results[2]['name'], 'Model_B')

    @patch('backend.app.database.pd.read_sql')
    @patch('backend.app.database.db.session')
    @patch('backend.app.database.app.app_context')
    def test_sorts_by_win_rate_ascending(self, mock_ctx, mock_session, mock_read_sql):
        mock_read_sql.return_value = self.df

        results = get_aggregated_stats(param='win_rate', ascending=True)

        self.assertEqual(results[0]['name'], 'Model_B')
        self.assertEqual(results[0]['win_rate'], 20.0)
        self.assertEqual(results[1]['name'], 'Model_C')
        self.assertEqual(results[2]['name'], 'Model_A')

    @patch('backend.app.database.pd.read_sql')
    @patch('backend.app.database.db.session')
    @patch('backend.app.database.app.app_context')
    def test_returns_unsorted_if_param_is_none(self, mock_ctx, mock_session, mock_read_sql):
        mock_read_sql.return_value = self.df

        results = get_aggregated_stats(param=None, ascending=True)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['name'], 'Model_A')


if __name__ == '__main__':
    unittest.main()