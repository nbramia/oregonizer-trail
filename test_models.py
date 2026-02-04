"""
Test suite for database models (User, Scenario)
"""
import unittest
import bcrypt
from app import app, db
from models import User, Scenario


class TestUserModel(unittest.TestCase):
    """Test cases for User model"""

    def setUp(self):
        """Set up test database before each test"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        with app.app_context():
            db.create_all()

        self.app = app
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        """Test creating a new user"""
        user = User(
            email='test@example.com',
            password=bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()
        )
        db.session.add(user)
        db.session.commit()

        retrieved_user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, 'test@example.com')
        self.assertTrue(bcrypt.checkpw('password123'.encode(), retrieved_user.password.encode()))

    def test_user_default_values(self):
        """Test that default values are set correctly"""
        user = User(
            email='test@example.com',
            password=bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()
        )
        db.session.add(user)
        db.session.commit()

        self.assertEqual(user.high_score, 0)
        self.assertEqual(user.games_played, 0)
        self.assertEqual(user.games_started, 0)
        self.assertIsNone(user.last_game_played)

    def test_user_email_unique(self):
        """Test that email must be unique"""
        user1 = User(
            email='test@example.com',
            password=bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()
        )
        db.session.add(user1)
        db.session.commit()

        user2 = User(
            email='test@example.com',
            password=bcrypt.hashpw('password456'.encode(), bcrypt.gensalt()).decode()
        )
        db.session.add(user2)

        with self.assertRaises(Exception):  # Should raise IntegrityError
            db.session.commit()

    def test_user_get_or_create_new(self):
        """Test get_or_create creates new user"""
        user_info = {
            'email': 'oauth@example.com',
            'sub': 'google-user-id-123'
        }

        user = User.get_or_create(user_info)

        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'oauth@example.com')
        self.assertIsNotNone(user.password)

    def test_user_get_or_create_existing(self):
        """Test get_or_create returns existing user"""
        existing_user = User(
            email='existing@example.com',
            password=bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()
        )
        db.session.add(existing_user)
        db.session.commit()

        user_info = {
            'email': 'existing@example.com',
            'sub': 'google-user-id-123'
        }

        user = User.get_or_create(user_info)

        self.assertEqual(user.id, existing_user.id)
        self.assertEqual(User.query.count(), 1)  # Should not create duplicate

    def test_user_repr(self):
        """Test user __repr__ method"""
        user = User(
            email='test@example.com',
            password=bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()
        )

        self.assertEqual(repr(user), '<User test@example.com>')


class TestScenarioModel(unittest.TestCase):
    """Test cases for Scenario model"""

    def setUp(self):
        """Set up test database before each test"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True

        with app.app_context():
            db.create_all()

        self.app = app
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_decision_scenario_creation(self):
        """Test creating a decision scenario"""
        import json

        metrics = json.dumps({
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
        })

        response = json.dumps({
            "yes": "You chose yes.",
            "no": "You chose no."
        })

        scenario = Scenario(
            name='test_decision',
            mode='Product Development',
            type='decision',
            text='Test decision scenario',
            metrics=metrics,
            response=response,
            community=False
        )

        db.session.add(scenario)
        db.session.commit()

        retrieved = Scenario.query.filter_by(name='test_decision').first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.type, 'decision')
        self.assertEqual(retrieved.mode, 'Product Development')
        self.assertFalse(retrieved.community)

    def test_informational_scenario_creation(self):
        """Test creating an informational scenario"""
        import json

        metrics = json.dumps({
            "staff_retention": -10,
            "partner_retention": -5,
            "partner_growth": 0,
            "tech_debt": 5
        })

        scenario = Scenario(
            name='test_informational',
            mode='Product Development',
            type='informational',
            text='Test informational scenario',
            metrics=metrics,
            response=None,
            community=False
        )

        db.session.add(scenario)
        db.session.commit()

        retrieved = Scenario.query.filter_by(name='test_informational').first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.type, 'informational')
        self.assertIsNone(retrieved.response)

    def test_scenario_name_unique(self):
        """Test that scenario name must be unique"""
        import json

        scenario1 = Scenario(
            name='duplicate_name',
            mode='Product Development',
            type='informational',
            text='First scenario',
            metrics=json.dumps({"staff_retention": 10}),
            community=False
        )
        db.session.add(scenario1)
        db.session.commit()

        scenario2 = Scenario(
            name='duplicate_name',
            mode='Product Development',
            type='informational',
            text='Second scenario',
            metrics=json.dumps({"staff_retention": 10}),
            community=False
        )
        db.session.add(scenario2)

        with self.assertRaises(Exception):  # Should raise IntegrityError
            db.session.commit()

    def test_scenario_repr(self):
        """Test scenario __repr__ method"""
        import json

        scenario = Scenario(
            name='test_scenario',
            mode='Product Development',
            type='informational',
            text='Test',
            metrics=json.dumps({"staff_retention": 10}),
            community=False
        )

        self.assertEqual(repr(scenario), '<Scenario test_scenario>')


if __name__ == '__main__':
    unittest.main()
