"""
Checks the scenario CSVs that populate_scenarios.py loads: every row must parse
and pass the same validation as a user-created scenario for its mode.
"""
import json
import unittest
from collections import Counter

from mode_config import MODES, get_enabled_modes
from populate_scenarios import load_all_mode_scenarios
from validation import (
    validate_scenario_name, validate_scenario_type, validate_scenario_text,
    validate_scenario_metrics, validate_scenario_response
)


class TestScenarioData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.scenarios = load_all_mode_scenarios()

    def test_names_are_unique(self):
        counts = Counter(s['name'] for s in self.scenarios)
        self.assertEqual([n for n, c in counts.items() if c > 1], [])

    def test_modes_are_known(self):
        known = {m['name'] for m in MODES}
        self.assertEqual({s['mode'] for s in self.scenarios} - known, set())

    def test_every_enabled_mode_has_both_types(self):
        for mode in get_enabled_modes():
            types = {s['type'] for s in self.scenarios if s['mode'] == mode}
            self.assertEqual(types, {'decision', 'informational'}, mode)

    def test_rows_validate_for_their_mode(self):
        for s in self.scenarios:
            with self.subTest(scenario=s['name']):
                validate_scenario_name(s['name'])
                validate_scenario_type(s['type'])
                validate_scenario_text(s['text'])
                validate_scenario_metrics(s['metrics'], s['type'], s['mode'])
                validate_scenario_response(s['response'], s['type'])

    def test_every_scenario_changes_something(self):
        for s in self.scenarios:
            with self.subTest(scenario=s['name']):
                metrics = json.loads(s['metrics'])
                if s['type'] == 'decision':
                    self.assertTrue(metrics['yes'] or metrics['no'])
                else:
                    self.assertTrue(metrics)


if __name__ == '__main__':
    unittest.main()
