"""
Tests for the input validators in validation.py
"""
import json
import unittest

from validation import (
    ValidationError, validate_difficulty, validate_turns_survived, validate_metric_value,
    validate_scenario_name, validate_scenario_mode, validate_scenario_type,
    validate_scenario_text, validate_scenario_metrics, validate_scenario_response
)


class TestValidation(unittest.TestCase):

    def test_difficulty(self):
        for value in ('Normal', 'Hard', 'Crazy'):
            self.assertEqual(validate_difficulty(value), value)
        for value in ('normal', 'Easy', None, ''):
            with self.assertRaises(ValidationError):
                validate_difficulty(value)

    def test_turns_survived(self):
        self.assertEqual(validate_turns_survived(0), 0)
        self.assertEqual(validate_turns_survived(25), 25)
        for value in (-1, 1001, '5', 2.5, None, True):
            with self.assertRaises(ValidationError, msg=repr(value)):
                validate_turns_survived(value)

    def test_metric_value(self):
        self.assertEqual(validate_metric_value(0, 'm'), 0)
        self.assertEqual(validate_metric_value(99.7, 'm'), 99)
        for value in (-1, 201, '50', None, True):
            with self.assertRaises(ValidationError, msg=repr(value)):
                validate_metric_value(value, 'm')

    def test_scenario_name(self):
        self.assertEqual(validate_scenario_name('  my_scenario '), 'my_scenario')
        for value in ('', None, 5, 'x' * 201):
            with self.assertRaises(ValidationError):
                validate_scenario_name(value)

    def test_scenario_mode_must_be_enabled(self):
        self.assertEqual(validate_scenario_mode('Movement Labs'), 'Movement Labs')
        for value in ('Product Development', 'Nope', None):
            with self.assertRaises(ValidationError):
                validate_scenario_mode(value)

    def test_scenario_type(self):
        self.assertEqual(validate_scenario_type('decision'), 'decision')
        self.assertEqual(validate_scenario_type('informational'), 'informational')
        with self.assertRaises(ValidationError):
            validate_scenario_type('other')

    def test_scenario_text(self):
        self.assertEqual(validate_scenario_text('Something happened'), 'Something happened')
        for value in ('', None, 'x' * 5001):
            with self.assertRaises(ValidationError):
                validate_scenario_text(value)

    def test_decision_metrics(self):
        good = json.dumps({'yes': {'revenue': 10}, 'no': {'net_votes': -10}})
        self.assertEqual(validate_scenario_metrics(good, 'decision', 'Movement Labs'), good)
        bad = [
            {'yes': {'revenue': 10}},                              # missing 'no'
            {'yes': {'partner_growth': 10}, 'no': {}},             # metric not in mode
            {'yes': {'revenue': 101}, 'no': {}},                   # out of range
            {'yes': {'revenue': '10'}, 'no': {}},                  # not a number
            {'yes': {'revenue': True}, 'no': {}},                  # bool is not a number
            {'yes': [], 'no': {}},                                 # not a dict
        ]
        for metrics in bad:
            with self.assertRaises(ValidationError, msg=metrics):
                validate_scenario_metrics(json.dumps(metrics), 'decision', 'Movement Labs')
        with self.assertRaises(ValidationError):
            validate_scenario_metrics('{not json', 'decision', 'Movement Labs')

    def test_informational_metrics(self):
        good = json.dumps({'staff_retention': -20, 'tech_debt': 5})
        self.assertEqual(validate_scenario_metrics(good, 'informational', 'Movement Labs'), good)
        for metrics in ({'partner_growth': 5}, {'revenue': -101}, ['revenue']):
            with self.assertRaises(ValidationError, msg=metrics):
                validate_scenario_metrics(json.dumps(metrics), 'informational', 'Movement Labs')

    def test_decision_response(self):
        good = json.dumps({'yes': 'Did it', 'no': "Didn't"})
        self.assertEqual(validate_scenario_response(good, 'decision'), good)
        for response in (None, '', json.dumps({'yes': 'only'}), json.dumps({'yes': 1, 'no': 'x'}), '{bad'):
            with self.assertRaises(ValidationError, msg=response):
                validate_scenario_response(response, 'decision')

    def test_informational_response_not_required(self):
        self.assertIsNone(validate_scenario_response(None, 'informational'))


if __name__ == '__main__':
    unittest.main()
