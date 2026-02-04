"""
Comprehensive tests for game-end scenarios
Tests all possible ways metrics can hit zero and message handling
"""
import unittest
from app import app, db
from game_logic import developmentGame


class TestGameEndScenarios(unittest.TestCase):
    """Test all game-end scenarios comprehensively"""

    def setUp(self):
        """Set up test game instance"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True

        with app.app_context():
            db.create_all()

        self.app = app
        self.app_context = app.app_context()
        self.app_context.push()
        self.game = developmentGame()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_single_failure_staff_retention(self):
        """Test failure when only staff retention hits zero"""
        self.game.staff_retention = 0
        self.game.partner_growth = 50
        self.game.partner_retention = 50
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("quit", status)
        self.assertNotIn("Also:", status)  # Should NOT have "Also:" for single failure
        self.assertNotIn("•", status)  # Should NOT have bullets for single failure

    def test_single_failure_partner_growth(self):
        """Test failure when only partner growth hits zero"""
        self.game.staff_retention = 50
        self.game.partner_growth = 0
        self.game.partner_retention = 50
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("progress", status)
        self.assertNotIn("Also:", status)

    def test_single_failure_partner_retention(self):
        """Test failure when only partner retention hits zero"""
        self.game.staff_retention = 50
        self.game.partner_growth = 50
        self.game.partner_retention = 0
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("renew", status)
        self.assertNotIn("Also:", status)

    def test_single_failure_tech_debt(self):
        """Test failure when only tech debt hits zero"""
        self.game.staff_retention = 50
        self.game.partner_growth = 50
        self.game.partner_retention = 50
        self.game.tech_debt = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("debt", status)
        self.assertNotIn("Also:", status)

    def test_double_failure_staff_and_partner_growth(self):
        """Test failure when both staff retention and partner growth hit zero"""
        self.game.staff_retention = 0
        self.game.partner_growth = 0
        self.game.partner_retention = 50
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("quit", status)
        self.assertIn("progress", status)
        self.assertIn("•", status)  # Should have bullets for multiple failures
        self.assertIn("Multiple critical issues", status)  # Should indicate multiple failures

    def test_double_failure_partner_growth_and_retention(self):
        """Test failure when both partner growth and retention hit zero"""
        self.game.staff_retention = 50
        self.game.partner_growth = 0
        self.game.partner_retention = 0
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("progress", status)
        self.assertIn("renew", status)
        self.assertIn("•", status)  # Should have bullets for multiple failures

    def test_triple_failure(self):
        """Test failure when three metrics hit zero"""
        self.game.staff_retention = 0
        self.game.partner_growth = 0
        self.game.partner_retention = 0
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("quit", status)
        self.assertIn("progress", status)
        self.assertIn("renew", status)
        # Should have bullets for all three failures
        self.assertEqual(status.count("•"), 3)  # Three bullets for three failures

    def test_total_failure_all_metrics_zero(self):
        """Test catastrophic failure when all metrics hit zero"""
        self.game.staff_retention = 0
        self.game.partner_growth = 0
        self.game.partner_retention = 0
        self.game.tech_debt = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("quit", status)
        self.assertIn("progress", status)
        self.assertIn("renew", status)
        self.assertIn("debt", status)
        # Should have four bullets for four failures
        self.assertEqual(status.count("•"), 4)

    def test_negative_metrics_treated_as_zero(self):
        """Test that negative metrics are treated same as zero"""
        self.game.staff_retention = -10
        self.game.partner_growth = -5
        self.game.partner_retention = 50
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("quit", status)
        self.assertIn("progress", status)

    def test_win_at_turn_25_overrides_failure(self):
        """Test that failure takes priority over survival win at turn 25"""
        self.game.turns_survived = 25
        self.game.staff_retention = 0  # This should cause failure
        self.game.partner_growth = 50
        self.game.partner_retention = 50
        self.game.tech_debt = 50

        status = self.game.check_status()

        # FIXED: Failure takes priority - should NOT show win message
        self.assertIn("Failure", status)
        self.assertNotIn("Congratulations", status)  # Should NOT show win message

    def test_thriving_win_with_one_metric_at_zero(self):
        """Test that failure takes priority over thriving win"""
        self.game.turns_survived = 12
        self.game.staff_retention = 110
        self.game.partner_growth = 105
        self.game.partner_retention = 115
        self.game.tech_debt = 0  # This should cause failure

        status = self.game.check_status()

        # FIXED: Failure takes priority - should NOT show thriving message
        self.assertIn("Failure", status)
        self.assertNotIn("thriving", status)  # Should NOT show thriving message

    def test_no_status_message_during_normal_play(self):
        """Test that no message appears during normal gameplay"""
        self.game.turns_survived = 5
        self.game.staff_retention = 80
        self.game.partner_growth = 70
        self.game.partner_retention = 60
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIsNone(status)

    def test_exact_zero_boundary(self):
        """Test exact zero boundary (not negative)"""
        self.game.staff_retention = 0
        self.game.partner_growth = 50
        self.game.partner_retention = 50
        self.game.tech_debt = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)

    def test_just_above_zero_no_failure(self):
        """Test that 0.01 above zero doesn't trigger failure"""
        self.game.staff_retention = 0.01
        self.game.partner_growth = 0.01
        self.game.partner_retention = 0.01
        self.game.tech_debt = 0.01

        status = self.game.check_status()

        self.assertIsNone(status)  # Should not fail

    def test_message_order_consistency(self):
        """Test that failure messages appear in consistent order"""
        self.game.staff_retention = 0
        self.game.partner_growth = 0
        self.game.partner_retention = 0
        self.game.tech_debt = 0

        status = self.game.check_status()

        # Messages should appear in order: staff, growth, retention, debt
        staff_pos = status.find("quit")
        growth_pos = status.find("progress")
        retention_pos = status.find("renew")
        debt_pos = status.find("debt")

        self.assertLess(staff_pos, growth_pos)
        self.assertLess(growth_pos, retention_pos)
        self.assertLess(retention_pos, debt_pos)


if __name__ == '__main__':
    unittest.main()
