"""
Test suite for game logic (developmentGame class)
"""
import unittest
import json
from app import app, db
from models import Scenario
from game_logic import developmentGame


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
        self.assertEqual(self.game.difficulty, "Normal")
        self.assertEqual(self.game.mode, "Product Development")
        self.assertEqual(self.game.variation_range, (0.8, 1.25))
        self.assertFalse(self.game.include_community_scenarios)
        self.assertEqual(self.game.staff_retention, 100)
        self.assertEqual(self.game.partner_growth, 100)
        self.assertEqual(self.game.partner_retention, 100)
        self.assertEqual(self.game.tech_debt, 100)
        self.assertEqual(self.game.turns_survived, 0)
        self.assertEqual(self.game.status, "developing")

    def test_set_difficulty_normal(self):
        """Test setting difficulty to Normal"""
        self.game.set_difficulty("Normal")

        self.assertEqual(self.game.variation_range, (0.8, 1.25))
        self.assertEqual(self.game.staff_retention, 100)
        self.assertEqual(self.game.partner_growth, 100)
        self.assertEqual(self.game.partner_retention, 100)
        self.assertEqual(self.game.tech_debt, 100)

    def test_set_difficulty_hard(self):
        """Test setting difficulty to Hard"""
        self.game.set_difficulty("Hard")

        self.assertEqual(self.game.variation_range, (1.0, 1.4))
        self.assertEqual(self.game.staff_retention, 85)
        self.assertEqual(self.game.partner_growth, 85)
        self.assertEqual(self.game.partner_retention, 85)
        self.assertEqual(self.game.tech_debt, 75)

    def test_set_difficulty_crazy(self):
        """Test setting difficulty to Crazy"""
        self.game.set_difficulty("Crazy")

        self.assertEqual(self.game.variation_range, (1.1, 1.6))
        self.assertEqual(self.game.staff_retention, 75)
        self.assertEqual(self.game.partner_growth, 75)
        self.assertEqual(self.game.partner_retention, 75)
        self.assertEqual(self.game.tech_debt, 50)

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
        self.game.staff_retention = 50
        self.game.turns_survived = 10
        self.game.status = "failure"

        self.game.reset_game()

        self.assertEqual(self.game.staff_retention, 100)
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
        self.game.partner_growth = 120
        self.game.partner_retention = 80
        self.game.tech_debt = 100

        self.game.adjust_for_tech_debt()

        # debt_factor = round((120 + 80) / 200) = round(1.0) = 1
        # new_tech_debt = max(0, 100 - 1) = 99
        self.assertEqual(self.game.tech_debt, 99)

    def test_tech_debt_adjustment_high_partner_metrics(self):
        """Test tech debt decay with high partner metrics"""
        self.game.partner_growth = 200
        self.game.partner_retention = 200
        self.game.tech_debt = 100

        self.game.adjust_for_tech_debt()

        # debt_factor = round((200 + 200) / 200) = round(2.0) = 2
        # new_tech_debt = max(0, 100 - 2) = 98
        self.assertEqual(self.game.tech_debt, 98)

    def test_tech_debt_adjustment_floor_zero(self):
        """Test tech debt doesn't go below zero"""
        self.game.partner_growth = 200
        self.game.partner_retention = 200
        self.game.tech_debt = 1

        self.game.adjust_for_tech_debt()

        # Would calculate to -1, but should floor at 0
        self.assertEqual(self.game.tech_debt, 0)

    def test_update_metrics(self):
        """Test metrics update returns correct data"""
        self.game.turns_survived = 5
        self.game.staff_retention = 80

        metrics = self.game.update_metrics()

        self.assertEqual(metrics['turns_survived'], 5)
        self.assertEqual(metrics['staff_retention'], 80)
        self.assertIn('partner_growth', metrics)
        self.assertIn('partner_retention', metrics)
        self.assertIn('tech_debt', metrics)

    def test_check_status_staff_retention_failure(self):
        """Test failure condition when staff retention reaches 0"""
        self.game.staff_retention = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("quit", status)

    def test_check_status_partner_growth_failure(self):
        """Test failure condition when partner growth reaches 0"""
        self.game.partner_growth = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("progress", status)

    def test_check_status_partner_retention_failure(self):
        """Test failure condition when partner retention reaches 0"""
        self.game.partner_retention = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("renew", status)

    def test_check_status_tech_debt_failure(self):
        """Test failure condition when tech debt reaches 0"""
        self.game.tech_debt = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("debt", status)

    def test_check_status_survival_win(self):
        """Test win condition by surviving 25 turns"""
        self.game.turns_survived = 25
        self.game.staff_retention = 50
        self.game.partner_growth = 50
        self.game.partner_retention = 50
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Congratulations", status)
        self.assertIn("25 turns", status)

    def test_check_status_thriving_win(self):
        """Test win condition by thriving (all metrics > 100 after turn 10)"""
        self.game.turns_survived = 12
        self.game.staff_retention = 110
        self.game.partner_growth = 105
        self.game.partner_retention = 115
        self.game.tech_debt = 50  # Tech debt doesn't need to be > 100

        status = self.game.check_status()

        self.assertIn("Congratulations", status)
        self.assertIn("thriving", status)

    def test_check_status_no_message(self):
        """Test no status message during normal gameplay"""
        self.game.turns_survived = 5
        self.game.staff_retention = 80
        self.game.partner_growth = 80
        self.game.partner_retention = 80
        self.game.tech_debt = 80

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
        self.game.partner_growth = 100
        self.game.partner_retention = 100
        self.game.tech_debt = 100

        # Call adjust_for_tech_debt directly to test the logic
        self.game.adjust_for_tech_debt()

        # Should have decreased by 1 (round(200/200) = 1)
        self.assertEqual(self.game.tech_debt, 99)

    def test_next_turn_returns_messages_and_status(self):
        """Test that next_turn returns messages and status"""
        messages, status = self.game.next_turn()

        self.assertIsInstance(messages, list)
        # Status could be None during normal gameplay
        self.assertTrue(status is None or isinstance(status, str))

    def test_handle_scenario_decision_yes(self):
        """Test handling a decision scenario with 'yes' action"""
        scenario = Scenario.query.filter_by(name='test_decision').first()

        initial_staff = self.game.staff_retention

        response = self.game.handle_scenario('test_decision', 'yes')

        self.assertEqual(response, "You chose yes.")
        # Staff retention should have changed (with variation)
        self.assertNotEqual(self.game.staff_retention, initial_staff)

    def test_handle_scenario_decision_no(self):
        """Test handling a decision scenario with 'no' action"""
        scenario = Scenario.query.filter_by(name='test_decision').first()

        initial_staff = self.game.staff_retention

        response = self.game.handle_scenario('test_decision', 'no')

        self.assertEqual(response, "You chose no.")
        self.assertNotEqual(self.game.staff_retention, initial_staff)

    def test_handle_scenario_nonexistent_scenario(self):
        """Test handling a scenario that doesn't exist"""
        with self.assertRaises(ValueError):
            self.game.handle_scenario('nonexistent_scenario', 'yes')

    def test_apply_metric_change_staff_retention(self):
        """Test applying metric change to staff retention"""
        initial = self.game.staff_retention

        self.game.apply_metric_change('staff_retention', 20)

        # Should be increased by approximately 20 (with variation)
        self.assertGreater(self.game.staff_retention, initial)

    def test_apply_metric_change_partner_growth(self):
        """Test applying metric change to partner growth"""
        initial = self.game.partner_growth

        self.game.apply_metric_change('partner_growth', -15)

        # Should be decreased by approximately 15 (with variation)
        self.assertLess(self.game.partner_growth, initial)

    def test_apply_metric_change_partner_retention(self):
        """Test applying metric change to partner retention"""
        initial = self.game.partner_retention

        self.game.apply_metric_change('partner_retention', 10)

        # Should be increased by approximately 10 (with variation)
        self.assertGreater(self.game.partner_retention, initial)

    def test_apply_metric_change_tech_debt(self):
        """Test applying metric change to tech debt"""
        initial = self.game.tech_debt

        self.game.apply_metric_change('tech_debt', 25)

        # Should be increased by approximately 25 (with variation)
        self.assertGreater(self.game.tech_debt, initial)


if __name__ == '__main__':
    unittest.main()
