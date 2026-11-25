"""
Comprehensive tests for game-end scenarios
Tests all possible ways metrics can hit zero and message handling.
Runs in Product Development mode (staff, partner retention, partner growth,
tech debt); test_game_logic.TestMovementLabsGame covers the default mode.
"""
import unittest
from app import app, db
from game_logic import developmentGame
from mode_config import get_mode_metrics


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
        self.game.set_mode('Product Development')

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_single_failure_staff_retention(self):
        """Test failure when only staff retention hits zero"""
        self.game.metrics['staff_retention'] = 0
        self.game.metrics['partner_growth'] = 50
        self.game.metrics['partner_retention'] = 50
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("STAFF RETENTION", status)
        self.assertNotIn("Multiple critical issues", status)  # Single failure uses the short form

    def test_single_failure_partner_growth(self):
        """Test failure when only partner growth hits zero"""
        self.game.metrics['staff_retention'] = 50
        self.game.metrics['partner_growth'] = 0
        self.game.metrics['partner_retention'] = 50
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("progress", status)
        self.assertNotIn("Multiple critical issues", status)

    def test_single_failure_partner_retention(self):
        """Test failure when only partner retention hits zero"""
        self.game.metrics['staff_retention'] = 50
        self.game.metrics['partner_growth'] = 50
        self.game.metrics['partner_retention'] = 0
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("renew", status)
        self.assertNotIn("Multiple critical issues", status)

    def test_single_failure_tech_debt(self):
        """Test failure when only tech debt hits zero"""
        self.game.metrics['staff_retention'] = 50
        self.game.metrics['partner_growth'] = 50
        self.game.metrics['partner_retention'] = 50
        self.game.metrics['tech_debt'] = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("TECH DEBT", status)
        self.assertNotIn("Multiple critical issues", status)

    def test_double_failure_staff_and_partner_growth(self):
        """Test failure when both staff retention and partner growth hit zero"""
        self.game.metrics['staff_retention'] = 0
        self.game.metrics['partner_growth'] = 0
        self.game.metrics['partner_retention'] = 50
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("STAFF RETENTION", status)
        self.assertIn("progress", status)
        self.assertIn("Multiple critical issues", status)  # Should indicate multiple failures

    def test_double_failure_partner_growth_and_retention(self):
        """Test failure when both partner growth and retention hit zero"""
        self.game.metrics['staff_retention'] = 50
        self.game.metrics['partner_growth'] = 0
        self.game.metrics['partner_retention'] = 0
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("progress", status)
        self.assertIn("renew", status)
        self.assertIn("Multiple critical issues", status)

    def test_triple_failure(self):
        """Test failure when three metrics hit zero"""
        self.game.metrics['staff_retention'] = 0
        self.game.metrics['partner_growth'] = 0
        self.game.metrics['partner_retention'] = 0
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("STAFF RETENTION", status)
        self.assertIn("progress", status)
        self.assertIn("renew", status)
        self.assertNotIn("TECH DEBT", status)

    def test_total_failure_all_metrics_zero(self):
        """Test catastrophic failure when all metrics hit zero"""
        self.game.metrics['staff_retention'] = 0
        self.game.metrics['partner_growth'] = 0
        self.game.metrics['partner_retention'] = 0
        self.game.metrics['tech_debt'] = 0

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("STAFF RETENTION", status)
        self.assertIn("progress", status)
        self.assertIn("renew", status)
        self.assertIn("TECH DEBT", status)
        self.assertIn("Multiple critical issues", status)

    def test_negative_metrics_treated_as_zero(self):
        """Test that negative metrics are treated same as zero"""
        self.game.metrics['staff_retention'] = -10
        self.game.metrics['partner_growth'] = -5
        self.game.metrics['partner_retention'] = 50
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)
        self.assertIn("STAFF RETENTION", status)
        self.assertIn("progress", status)

    def test_failure_overrides_win_at_turn_25(self):
        """Test that failure takes priority over survival win at turn 25"""
        self.game.turns_survived = 25
        self.game.metrics['staff_retention'] = 0  # This should cause failure
        self.game.metrics['partner_growth'] = 50
        self.game.metrics['partner_retention'] = 50
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        # Failure takes priority over the survival win
        self.assertIn("Failure", status)
        self.assertNotIn("Congratulations", status)  # Should NOT show win message

    def test_failure_overrides_thriving_win(self):
        """Test that failure takes priority over thriving win"""
        self.game.turns_survived = 12
        self.game.metrics['staff_retention'] = 100
        self.game.metrics['partner_growth'] = 100
        self.game.metrics['partner_retention'] = 100
        self.game.metrics['tech_debt'] = 0  # This should cause failure

        status = self.game.check_status()

        # Failure takes priority over the thriving win
        self.assertIn("Failure", status)
        self.assertNotIn("thriving", status)  # Should NOT show thriving message

    def test_no_status_message_during_normal_play(self):
        """Test that no message appears during normal gameplay"""
        self.game.turns_survived = 5
        self.game.metrics['staff_retention'] = 80
        self.game.metrics['partner_growth'] = 70
        self.game.metrics['partner_retention'] = 60
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIsNone(status)

    def test_exact_zero_boundary(self):
        """Test exact zero boundary (not negative)"""
        self.game.metrics['staff_retention'] = 0
        self.game.metrics['partner_growth'] = 50
        self.game.metrics['partner_retention'] = 50
        self.game.metrics['tech_debt'] = 50

        status = self.game.check_status()

        self.assertIn("Failure", status)

    def test_just_above_zero_no_failure(self):
        """Test that 0.01 above zero doesn't trigger failure"""
        self.game.metrics['staff_retention'] = 0.01
        self.game.metrics['partner_growth'] = 0.01
        self.game.metrics['partner_retention'] = 0.01
        self.game.metrics['tech_debt'] = 0.01

        status = self.game.check_status()

        self.assertIsNone(status)  # Should not fail

    def test_message_order_consistency(self):
        """Test that failure messages appear in consistent order"""
        self.game.metrics['staff_retention'] = 0
        self.game.metrics['partner_growth'] = 0
        self.game.metrics['partner_retention'] = 0
        self.game.metrics['tech_debt'] = 0

        status = self.game.check_status()

        # Messages follow the mode's metric order
        labels = {
            'staff_retention': "STAFF RETENTION",
            'partner_retention': "PARTNER RETENTION",
            'partner_growth': "PARTNER GROWTH",
            'tech_debt': "TECH DEBT",
        }
        positions = [status.find(labels[m]) for m in get_mode_metrics('Product Development')]

        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))

if __name__ == '__main__':
    unittest.main()
