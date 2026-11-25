"""
Tests for saving and restoring a game (developmentGame.to_state / from_state),
which is how a game survives between serverless requests.
"""
import json
import unittest

from app import app, db
from models import Scenario
from game_logic import developmentGame


def _scenario(name, type_='decision'):
    if type_ == 'decision':
        metrics = {"yes": {"revenue": 10}, "no": {"revenue": -10}}
        response = json.dumps({"yes": "Y", "no": "N"})
    else:
        metrics = {"revenue": -5}
        response = None
    return Scenario(name=name, mode='Movement Labs', type=type_, text=name,
                    metrics=json.dumps(metrics), response=response, community=False)


class TestGameState(unittest.TestCase):

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        db.session.add_all([_scenario(f'd{i}') for i in range(5)] +
                           [_scenario(f'i{i}', 'informational') for i in range(3)])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_round_trip_preserves_game(self):
        game = developmentGame()
        game.set_difficulty('Hard')
        game.next_turn()
        game.next_turn()

        state = json.loads(json.dumps(game.to_state()))  # must be JSON-safe
        restored = developmentGame.from_state(state)

        self.assertEqual(restored.to_state(), game.to_state())
        self.assertEqual(restored.current_scenario.id, game.current_scenario.id)
        self.assertEqual([s.id for s in restored.decision_scenarios_queue],
                         [s.id for s in game.decision_scenarios_queue])

    def test_restored_game_continues_the_same_deck(self):
        game = developmentGame()
        game.next_turn()
        expected_next = game.decision_scenarios_queue[0].id

        restored = developmentGame.from_state(game.to_state())
        restored.last_scenario_was_informational = True  # force a decision
        restored.get_scenario()

        self.assertEqual(restored.current_scenario.id, expected_next)

    def test_rebuilds_deck_when_scenarios_were_reloaded(self):
        game = developmentGame()
        game.next_turn()
        state = game.to_state()

        # populate_scenarios.py replaces rows; on Postgres the new rows get new IDs
        Scenario.query.delete()
        new_d, new_i = _scenario('new_d'), _scenario('new_i', 'informational')
        new_d.id, new_i.id = 1000, 1001
        db.session.add_all([new_d, new_i])
        db.session.commit()

        restored = developmentGame.from_state(state)

        self.assertEqual([s.name for s in restored.decision_scenarios], ['new_d'])
        self.assertIsNone(restored.current_scenario)
        self.assertEqual(restored.metrics, game.metrics)
        self.assertEqual(restored.turns_survived, 1)

    def test_reused_ids_never_mix_scenario_types(self):
        game = developmentGame()
        game.next_turn()
        state = game.to_state()

        # SQLite reuses IDs after a reload, so saved decision IDs can now be informational rows
        Scenario.query.delete()
        db.session.add_all([_scenario(f'new_i{i}', 'informational') for i in range(5)] +
                           [_scenario(f'new_d{i}') for i in range(3)])
        db.session.commit()

        restored = developmentGame.from_state(state)

        self.assertTrue(restored.decision_scenarios)
        self.assertTrue(all(s.type == 'decision' for s in restored.decision_scenarios + restored.decision_scenarios_queue))
        self.assertTrue(all(s.type == 'informational' for s in restored.informational_scenarios + restored.informational_scenarios_queue))


    def test_empty_saved_queue_refills_from_deck(self):
        game = developmentGame()
        game.decision_scenarios_queue = []
        game.last_scenario_was_informational = True  # force a decision

        restored = developmentGame.from_state(game.to_state())

        self.assertEqual(restored.get_scenario().type, 'decision')


if __name__ == '__main__':
    unittest.main()
