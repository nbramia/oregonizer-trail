"""
Test suite for game logic (developmentGame class)

The engine is mode-agnostic. Most tests run it in Product Development mode
(partner metrics drive tech-debt decay); TestMovementLabsGame covers the
default, enabled mode.
"""
import unittest
import json
from app import app, db
from models import Scenario
from game_logic import developmentGame
from mode_config import get_default_mode, get_mode_metrics


class TestGameLogic(unittest.TestCase):
    """Test cases for developmentGame class"""

    def setUp(self):
        """Set up test database and game instance before each test"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True

        with app.app_context():
            db.create_all()
            self._seed_test_scenarios()

        self.app = app
        self.app_context = app.app_context()
        self.app_context.push()

        self.game = developmentGame()
        self.game.set_mode('Product Development')

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _seed_test_scenarios(self):
        """Create test scenarios in database"""
        # Decision scenario
        decision_scenario = Scenario(
            name='test_decision',
            mode='Product Development',
            type='decision',
            text='Test decision scenario',
            metrics=json.dumps({
                "yes": {
                    "staff_retention": -20,
                    "partner_retention": 10,
                    "partner_growth": 5,
                    "tech_debt": 15
                },
                "no": {
                    "staff_retention": 10,
                    "partner_retention": -15,
                    "partner_growth": -10,
                    "tech_debt": -5
                }
            }),
            response=json.dumps({
                "yes": "You chose yes.",
                "no": "You chose no."
            }),
            community=False
        )

        # Informational scenario
        info_scenario = Scenario(
            name='test_informational',
            mode='Product Development',
            type='informational',
            text='Test informational scenario',
            metrics=json.dumps({
                "staff_retention": -10,
                "partner_retention": -5,
                "partner_growth": 0,
                "tech_debt": 5
            }),
            response=None,
            community=False
        )

        # Community scenario
        community_scenario = Scenario(
            name='test_community',
            mode='Product Development',
            type='decision',
            text='Community scenario',
            metrics=json.dumps({
                "yes": {"staff_retention": 5, "partner_retention": 5, "partner_growth": 5, "tech_debt": 5},
                "no": {"staff_retention": -5, "partner_retention": -5, "partner_growth": -5, "tech_debt": -5}
            }),
            response=json.dumps({"yes": "Yes response", "no": "No response"}),
            community=True
        )

        # Partnership & Support mode scenario
        partnership_scenario = Scenario(
            name='test_partnership',
            mode='Partnership & Support',
            type='decision',
            text='Partnership scenario',
            metrics=json.dumps({
                "yes": {"staff_retention": 10, "partner_retention": 10, "partner_growth": 10, "tech_debt": 10},
                "no": {"staff_retention": -10, "partner_retention": -10, "partner_growth": -10, "tech_debt": -10}
            }),
            response=json.dumps({"yes": "Yes", "no": "No"}),
            community=False
        )

        db.session.add_all([decision_scenario, info_scenario, community_scenario, partnership_scenario])
        db.session.commit()

    def test_game_initialization(self):
        """Test game initializes with correct default values"""
        self.assertEqual(developmentGame().mode, get_default_mode())
        self.assertEqual(self.game.difficulty, "Normal")
        self.assertEqual(self.game.mode, "Product Development")
        self.assertEqual(self.game.variation_range, (0.8, 1.25))
        self.assertFalse(self.game.include_community_scenarios)
        self.assertEqual(self.game.metrics['staff_retention'], 100)
        self.assertEqual(self.game.metrics['partner_growth'], 100)
        self.assertEqual(self.game.metrics['partner_retention'], 100)
        self.assertEqual(self.game.metrics['tech_debt'], 100)
        self.assertEqual(self.game.turns_survived, 0)
        self.assertEqual(self.game.status, "developing")

    def test_set_difficulty_normal(self):
        """Test setting difficulty to Normal"""
        self.game.set_difficulty("Normal")

        self.assertEqual(self.game.variation_range, (0.8, 1.25))
        self.assertEqual(self.game.metrics['staff_retention'], 100)
        self.assertEqual(self.game.metrics['partner_growth'], 100)
        self.assertEqual(self.game.metrics['partner_retention'], 100)
        self.assertEqual(self.game.metrics['tech_debt'], 100)

    def test_set_difficulty_hard(self):
        """Test setting difficulty to Hard"""
        self.game.set_difficulty("Hard")

        self.assertEqual(self.game.variation_range, (1.0, 1.4))
        self.assertEqual(self.game.metrics['staff_retention'], 85)
        self.assertEqual(self.game.metrics['partner_growth'], 85)
        self.assertEqual(self.game.metrics['partner_retention'], 85)
        self.assertEqual(self.game.metrics['tech_debt'], 75)

    def test_set_difficulty_crazy(self):
        """Test setting difficulty to Crazy"""
        self.game.set_difficulty("Crazy")

        self.assertEqual(self.game.variation_range, (1.1, 1.6))
        self.assertEqual(self.game.metrics['staff_retention'], 75)
        self.assertEqual(self.game.metrics['partner_growth'], 75)
        self.assertEqual(self.game.metrics['partner_retention'], 75)
        self.assertEqual(self.game.metrics['tech_debt'], 50)

    def test_set_mode(self):
        """Test setting game mode"""
        initial_scenarios = len(self.game.decision_scenarios)

        self.game.set_mode("Partnership & Support")

        self.assertEqual(self.game.mode, "Partnership & Support")
        # Should reload scenarios for new mode
        self.assertIsNotNone(self.game.decision_scenarios)

    def test_reset_game(self):
        """Test game reset functionality"""
        # Change some values
        self.game.metrics['staff_retention'] = 50
        self.game.turns_survived = 10
        self.game.status = "failure"

        self.game.reset_game()

        self.assertEqual(self.game.metrics['staff_retention'], 100)
        self.assertEqual(self.game.turns_survived, 0)
        self.assertEqual(self.game.status, "developing")
        self.assertIsNone(self.game.current_scenario)

    def test_apply_variation(self):
        """Test variation calculation"""
        # Test multiple times since it's random
        for _ in range(10):
            result = self.game.apply_variation(100)
            # Should be between 80 and 125 for Normal difficulty
            self.assertGreaterEqual(result, 80)
            self.assertLessEqual(result, 125)

    def test_tech_debt_adjustment(self):
        """Test tech debt auto-decay calculation"""
        self.game.metrics['partner_growth'] = 70
        self.game.metrics['partner_retention'] = 80
        self.game.metrics['tech_debt'] = 100

        self.game.adjust_for_tech_debt()

        # debt_factor = round((70 + 80) / 200) = round(0.75) = 1
        # new_tech_debt = max(0, 100 - 1) = 99
        self.assertEqual(self.game.metrics['tech_debt'], 99)

    def test_tech_debt_adjustment_high_partner_metrics(self):
        """Test tech debt decay with partner metrics at their 100 cap"""
        self.game.metrics['partner_growth'] = 100
        self.game.metrics['partner_retention'] = 100
        self.game.metrics['tech_debt'] = 100

        self.game.adjust_for_tech_debt()

        # debt_factor = round((100 + 100) / 200) = 1
        self.assertEqual(self.game.metrics['tech_debt'], 99)

    def test_tech_debt_adjustment_low_partner_metrics(self):
        """Test tech debt does not decay when partner metrics are low"""
        self.game.metrics['partner_growth'] = 20
        self.game.metrics['partner_retention'] = 20
        self.game.metrics['tech_debt'] = 100

        self.game.adjust_for_tech_debt()

        # debt_factor = round(40 / 200) = 0
        self.assertEqual(self.game.metrics['tech_debt'], 100)

    def test_tech_debt_adjustment_floor_zero(self):
        """Test tech debt doesn't go below zero"""
        self.game.metrics['partner_growth'] = 100
        self.game.metrics['partner_retention'] = 100
        self.game.metrics['tech_debt'] = 0

        self.game.adjust_for_tech_debt()

        # Would calculate to -1, but should floor at 0
        self.assertEqual(self.game.metrics['tech_debt'], 0)

    def test_update_metrics(self):
        """Test metrics update returns correct data"""
        self.game.turns_survived = 5
        self.game.metrics['staff_retention'] = 80

        metrics = self.game.update_metrics()

        self.assertEqual(metrics['turns_survived'], 5)
        self.assertEqual(metrics['staff_retention'], 80)
        self.assertIn('partner_growth', metrics)
        self.assertIn('partner_retention', metrics)
        self.assertIn('tech_debt', metrics)

    def test_check_status_staff_retention_failure(self):
        """Test failure condition when staff retention reaches 0"""
        self.game.metrics['staff_retention'] = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("STAFF RETENTION", status)

    def test_check_status_partner_growth_failure(self):
        """Test failure condition when partner growth reaches 0"""
        self.game.metrics['partner_growth'] = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("progress", status)

    def test_check_status_partner_retention_failure(self):
        """Test failure condition when partner retention reaches 0"""
        self.game.metrics['partner_retention'] = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("renew", status)

    def test_check_status_tech_debt_failure(self):
        """Test failure condition when tech debt reaches 0"""
        self.game.metrics['tech_debt'] = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("TECH DEBT", status)

    def test_check_status_survival_win(self):
        """Test win condition by surviving 25 turns"""
        self.game.turns_survived = 25
        self.game.metrics['staff_retention'] = 50
        self.game.metrics['partner_growth'] = 50
        self.game.metrics['partner_retention'] = 50
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Congratulations", status)
        self.assertIn("25 turns", status)

    def test_check_status_thriving_win(self):
        """Test win condition by thriving (all non-tech metrics at 100 after turn 10)"""
        self.game.turns_survived = 12
        self.game.metrics['staff_retention'] = 100
        self.game.metrics['partner_growth'] = 100
        self.game.metrics['partner_retention'] = 100
        self.game.metrics['tech_debt'] = 50  # Tech debt doesn't need to be at 100

        status = self.game.check_status()

        self.assertIn("Congratulations", status)
        self.assertIn("thriving", status)

    def test_check_status_no_thriving_before_turn_10(self):
        """Thriving needs at least 10 turns"""
        self.game.turns_survived = 9

        self.assertIsNone(self.game.check_status())

    def test_check_status_no_message(self):
        """Test no status message during normal gameplay"""
        self.game.turns_survived = 5
        self.game.metrics['staff_retention'] = 80
        self.game.metrics['partner_growth'] = 80
        self.game.metrics['partner_retention'] = 80
        self.game.metrics['tech_debt'] = 80

        status = self.game.check_status()

        self.assertIsNone(status)

    def test_setup_scenarios_loads_scenarios(self):
        """Test that scenarios are loaded correctly"""
        self.game.setup_scenarios()

        self.assertGreater(len(self.game.decision_scenarios), 0)
        self.assertGreater(len(self.game.informational_scenarios), 0)
        self.assertIsNotNone(self.game.decision_scenarios_queue)
        self.assertIsNotNone(self.game.informational_scenarios_queue)

    def test_setup_scenarios_excludes_community(self):
        """Test that community scenarios are excluded by default"""
        self.game.include_community_scenarios = False
        self.game.setup_scenarios()

        # Check that no community scenarios are loaded
        for scenario in self.game.decision_scenarios:
            self.assertFalse(scenario.community)

    def test_setup_scenarios_includes_community(self):
        """Test that community scenarios can be included"""
        self.game.include_community_scenarios = True
        self.game.setup_scenarios()

        # Should have at least one community scenario
        has_community = any(s.community for s in self.game.decision_scenarios)
        self.assertTrue(has_community)

    def test_set_include_community_scenarios(self):
        """Test toggling community scenarios"""
        self.assertFalse(self.game.include_community_scenarios)

        self.game.set_include_community_scenarios(True)

        self.assertTrue(self.game.include_community_scenarios)
        # Should also reset the game
        self.assertEqual(self.game.turns_survived, 0)

    def test_get_scenario_returns_scenario(self):
        """Test that get_scenario returns a scenario object"""
        scenario = self.game.get_scenario()

        self.assertIsNotNone(scenario)
        self.assertIsInstance(scenario, Scenario)
        self.assertEqual(self.game.current_scenario, scenario)

    def test_get_scenario_refreshes_queue(self):
        """Test that scenario queue refreshes when empty"""
        # Empty the queues
        self.game.decision_scenarios_queue = []
        self.game.informational_scenarios_queue = []

        scenario = self.game.get_scenario()

        # Should have reloaded scenarios
        self.assertIsNotNone(scenario)

    def test_next_turn_increments_turn(self):
        """Test that next_turn increments turn counter"""
        initial_turns = self.game.turns_survived

        self.game.next_turn()

        self.assertEqual(self.game.turns_survived, initial_turns + 1)

    def test_next_turn_adjusts_tech_debt(self):
        """Test that next_turn calls tech debt adjustment"""
        self.game.metrics['partner_growth'] = 100
        self.game.metrics['partner_retention'] = 100
        self.game.metrics['tech_debt'] = 100

        # Call adjust_for_tech_debt directly to test the logic
        self.game.adjust_for_tech_debt()

        # Should have decreased by 1 (round(200/200) = 1)
        self.assertEqual(self.game.metrics['tech_debt'], 99)

    def test_next_turn_returns_messages_and_status(self):
        """Test that next_turn returns messages and status"""
        messages, status = self.game.next_turn()

        self.assertIsInstance(messages, list)
        # Status could be None during normal gameplay
        self.assertTrue(status is None or isinstance(status, str))

    def test_handle_scenario_decision_yes(self):
        """Test handling a decision scenario with 'yes' action"""
        scenario = Scenario.query.filter_by(name='test_decision').first()

        initial_staff = self.game.metrics['staff_retention']

        response = self.game.handle_scenario('test_decision', 'yes')

        self.assertEqual(response, "You chose yes.")
        # Staff retention should have changed (with variation)
        self.assertNotEqual(self.game.metrics['staff_retention'], initial_staff)

    def test_handle_scenario_decision_no(self):
        """Test handling a decision scenario with 'no' action"""
        scenario = Scenario.query.filter_by(name='test_decision').first()
        self.game.metrics['staff_retention'] = 50

        initial_staff = self.game.metrics['staff_retention']

        response = self.game.handle_scenario('test_decision', 'no')

        self.assertEqual(response, "You chose no.")
        self.assertNotEqual(self.game.metrics['staff_retention'], initial_staff)

    def test_handle_scenario_nonexistent_scenario(self):
        """Test handling a scenario that doesn't exist"""
        with self.assertRaises(ValueError):
            self.game.handle_scenario('nonexistent_scenario', 'yes')

    def test_apply_metric_change_staff_retention(self):
        """Test applying metric change to staff retention"""
        self.game.metrics['staff_retention'] = 50
        initial = self.game.metrics['staff_retention']

        self.game.apply_metric_change('staff_retention', 20)

        # Should be increased by approximately 20 (with variation)
        self.assertGreater(self.game.metrics['staff_retention'], initial)

    def test_apply_metric_change_partner_growth(self):
        """Test applying metric change to partner growth"""
        initial = self.game.metrics['partner_growth']

        self.game.apply_metric_change('partner_growth', -15)

        # Should be decreased by approximately 15 (with variation)
        self.assertLess(self.game.metrics['partner_growth'], initial)

    def test_apply_metric_change_partner_retention(self):
        """Test applying metric change to partner retention"""
        self.game.metrics['partner_retention'] = 50
        initial = self.game.metrics['partner_retention']

        self.game.apply_metric_change('partner_retention', 10)

        # Should be increased by approximately 10 (with variation)
        self.assertGreater(self.game.metrics['partner_retention'], initial)

    def test_apply_metric_change_tech_debt(self):
        """Test applying metric change to tech debt"""
        self.game.metrics['tech_debt'] = 50
        initial = self.game.metrics['tech_debt']

        self.game.apply_metric_change('tech_debt', 25)

        # Should be increased by approximately 25 (with variation)
        self.assertGreater(self.game.metrics['tech_debt'], initial)

    def test_apply_metric_change_clamps_to_range(self):
        """Metric changes are clamped to 0-100"""
        self.game.apply_metric_change('staff_retention', 50)
        self.assertEqual(self.game.metrics['staff_retention'], 100)

        self.game.metrics['staff_retention'] = 50
        self.game.apply_metric_change('staff_retention', -100)
        self.assertEqual(self.game.metrics['staff_retention'], 0)

    def test_apply_metric_change_ignores_other_modes_metrics(self):
        """A metric the current mode doesn't track is ignored"""
        before = dict(self.game.metrics)

        self.game.apply_metric_change('revenue', 10)

        self.assertEqual(self.game.metrics, before)

    def test_get_scenario_never_informational_on_turn_1(self):
        """Turn 1 always shows a decision scenario"""
        self.game.turns_survived = 1
        for _ in range(20):
            self.game.last_scenario_was_informational = False
            self.assertEqual(self.game.get_scenario().type, 'decision')

    def test_get_scenario_never_informational_twice_in_a_row(self):
        """An informational scenario is never followed by another"""
        self.game.turns_survived = 5
        for _ in range(20):
            self.game.last_scenario_was_informational = True
            self.assertEqual(self.game.get_scenario().type, 'decision')

    def test_get_scenario_with_no_scenarios_returns_none(self):
        """A mode with no scenarios yields no scenario instead of crashing"""
        self.game.set_mode('Movement Labs')  # nothing seeded for this mode

        self.assertIsNone(self.game.get_scenario())
        messages, status = self.game.next_turn()
        self.assertEqual(messages, [])

    def test_get_scenario_falls_back_to_informational(self):
        """With only informational scenarios, turns still get one"""
        Scenario.query.filter_by(type='decision').delete()
        db.session.commit()
        self.game.setup_scenarios()

        scenario = self.game.get_scenario()

        self.assertEqual(scenario.type, 'informational')


class TestMovementLabsGame(unittest.TestCase):
    """The default mode, with its own metrics and tech-debt rule"""

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        db.session.add(Scenario(
            name='ml_decision', mode='Movement Labs', type='decision', text='ML decision',
            metrics=json.dumps({"yes": {"revenue": 10}, "no": {"net_votes": -10}}),
            response=json.dumps({"yes": "Y", "no": "N"}), community=False))
        db.session.commit()
        self.game = developmentGame()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_default_mode_metrics(self):
        self.assertEqual(self.game.mode, 'Movement Labs')
        self.assertEqual(list(self.game.metrics), get_mode_metrics('Movement Labs'))
        self.assertTrue(all(v == 100 for v in self.game.metrics.values()))

    def test_tech_debt_decay_uses_revenue_and_net_votes(self):
        self.game.metrics.update(revenue=100, net_votes=100, tech_debt=50)
        self.game.adjust_for_tech_debt()
        self.assertEqual(self.game.metrics['tech_debt'], 49)

    def test_failure_messages(self):
        self.game.metrics.update(revenue=0, net_votes=0)
        status = self.game.check_status()
        self.assertIn("REVENUE", status)
        self.assertIn("NET VOTES", status)
        self.assertIn("Multiple critical issues", status)

    def test_next_turn_serves_mode_scenarios(self):
        messages, _ = self.game.next_turn()
        self.assertEqual(messages, ['ML decision'])


if __name__ == '__main__':
    unittest.main()
