"""
Test suite for Flask routes and API endpoints
"""
import unittest
import json
import bcrypt
from app import app, db
from models import User, Scenario
from flask_login import login_user


class TestRoutes(unittest.TestCase):
    """Test cases for Flask routes"""

    def setUp(self):
        """Set up test client and database before each test"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'

        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            self._seed_test_data()

        self.app = app
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _seed_test_data(self):
        """Create test data"""
        # Create test user
        user = User(
            email='test@example.com',
            password=bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode(),
            high_score=50,
            games_played=5,
            games_started=10
        )
        db.session.add(user)

        # Create test scenarios
        decision_scenario = Scenario(
            name='test_decision',
            mode='Product Development',
            type='decision',
            text='Test decision',
            metrics=json.dumps({
                "yes": {"staff_retention": 10, "partner_retention": 5, "partner_growth": 5, "tech_debt": 5},
                "no": {"staff_retention": -10, "partner_retention": -5, "partner_growth": -5, "tech_debt": -5}
            }),
            response=json.dumps({"yes": "Yes response", "no": "No response"}),
            community=False
        )

        info_scenario = Scenario(
            name='test_info',
            mode='Product Development',
            type='informational',
            text='Test info',
            metrics=json.dumps({"staff_retention": -5, "partner_retention": -5, "partner_growth": -5, "tech_debt": 5}),
            community=False
        )

        db.session.add_all([decision_scenario, info_scenario])
        db.session.commit()

    def _login(self):
        """Helper method to log in a test user"""
        return self.client.post('/', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

    def test_index_get_unauthenticated(self):
        """Test GET request to index when not authenticated"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)

    def test_index_post_valid_credentials(self):
        """Test POST login with valid credentials"""
        response = self.client.post('/', data={
            'email': 'test@example.com',
            'password': 'password123'
        })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['authenticated'])

    def test_index_post_invalid_credentials(self):
        """Test POST login with invalid credentials"""
        response = self.client.post('/', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data['authenticated'])

    def test_check_auth_unauthenticated(self):
        """Test check_auth endpoint when not authenticated"""
        response = self.client.get('/check_auth')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['authenticated'])

    def test_check_auth_authenticated(self):
        """Test check_auth endpoint when authenticated"""
        self._login()

        response = self.client.get('/check_auth')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['authenticated'])
        self.assertEqual(data['email'], 'test@example.com')

    def test_login_endpoint(self):
        """Test /login endpoint"""
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['authenticated'])

    def test_logout_endpoint(self):
        """Test /logout endpoint"""
        self._login()

        response = self.client.post('/logout')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)

    def test_reset_game_authenticated(self):
        """Test /reset_game endpoint when authenticated"""
        self._login()

        response = self.client.post('/reset_game')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('metrics', data)
        self.assertEqual(data['metrics']['turns_survived'], 0)

    def test_reset_game_unauthenticated(self):
        """Test /reset_game endpoint when not authenticated"""
        response = self.client.post('/reset_game')

        # Should redirect to login (Flask-Login returns 302)
        self.assertEqual(response.status_code, 302)

    def test_next_turn(self):
        """Test /next_turn endpoint"""
        response = self.client.post('/next_turn')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Should return scenario data
        self.assertIn('metrics', data)
        self.assertIn('scenario_id', data)

    def test_set_difficulty_authenticated(self):
        """Test /set_difficulty endpoint when authenticated"""
        self._login()

        response = self.client.post('/set_difficulty',
                                     data=json.dumps({'difficulty': 'Hard'}),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('metrics', data)
        self.assertIn('message', data)

    def test_set_difficulty_unauthenticated(self):
        """Test /set_difficulty endpoint when not authenticated"""
        response = self.client.post('/set_difficulty',
                                     data=json.dumps({'difficulty': 'Hard'}),
                                     content_type='application/json')

        # Should require authentication (Flask-Login returns 302)
        self.assertEqual(response.status_code, 302)

    def test_handle_scenario(self):
        """Test /handle_scenario endpoint"""
        scenario = Scenario.query.filter_by(name='test_decision').first()

        response = self.client.post('/handle_scenario',
                                     data=json.dumps({
                                         'scenario': scenario.id,
                                         'action': 'yes'
                                     }),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('metrics', data)
        self.assertIn('message', data)

    def test_handle_scenario_invalid_id(self):
        """Test /handle_scenario with invalid scenario ID"""
        response = self.client.post('/handle_scenario',
                                     data=json.dumps({
                                         'scenario': 99999,
                                         'action': 'yes'
                                     }),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 500)

    def test_end_game_authenticated(self):
        """Test /end_game endpoint when authenticated"""
        self._login()

        response = self.client.post('/end_game',
                                     data=json.dumps({
                                         'turns_survived': 10,
                                         'difficulty': 'Normal',
                                         'won': False,
                                         'partner_retention': 50,
                                         'staff_retention': 50,
                                         'partner_growth': 50,
                                         'tech_debt': 50
                                     }),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('scores', data)
        self.assertIn('high_score', data)

        # Verify user stats were updated
        user = User.query.filter_by(email='test@example.com').first()
        self.assertEqual(user.games_played, 6)  # Was 5, now 6

    def test_end_game_updates_high_score(self):
        """Test that end_game updates high score when exceeded"""
        self._login()

        # Submit a high score
        response = self.client.post('/end_game',
                                     data=json.dumps({
                                         'turns_survived': 25,
                                         'difficulty': 'Crazy',
                                         'won': True,
                                         'partner_retention': 100,
                                         'staff_retention': 100,
                                         'partner_growth': 100,
                                         'tech_debt': 100
                                     }),
                                     content_type='application/json')

        data = json.loads(response.data)
        high_score = data['high_score']

        # Should be higher than initial 50
        self.assertGreater(high_score, 50)

    def test_get_user_info_authenticated(self):
        """Test /get_user_info endpoint when authenticated"""
        self._login()

        response = self.client.get('/get_user_info')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['high_score'], 50)
        self.assertEqual(data['games_played'], 5)

    def test_get_user_info_unauthenticated(self):
        """Test /get_user_info endpoint when not authenticated"""
        response = self.client.get('/get_user_info')

        # Should require authentication (Flask-Login returns 302)
        self.assertEqual(response.status_code, 302)

    def test_get_leaderboard_authenticated(self):
        """Test /get_leaderboard endpoint when authenticated"""
        self._login()

        response = self.client.get('/get_leaderboard')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['email'], 'test@example.com')

    def test_set_mode_authenticated(self):
        """Test /set_mode endpoint when authenticated"""
        self._login()

        response = self.client.post('/set_mode',
                                     data=json.dumps({'mode': 'Partnership & Support'}),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('metrics', data)
        self.assertIn('message', data)

    def test_get_modes_authenticated(self):
        """Test /get_modes endpoint when authenticated"""
        self._login()

        response = self.client.get('/get_modes')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('modes', data)
        self.assertIn('Product Development', data['modes'])

    def test_create_scenario_authenticated(self):
        """Test /create_scenario endpoint when authenticated"""
        self._login()

        new_scenario = {
            'name': 'new_test_scenario',
            'mode': 'Product Development',
            'type': 'informational',
            'text': 'New test scenario',
            'metrics': {
                'staff_retention': 10,
                'partner_retention': 5,
                'partner_growth': 5,
                'tech_debt': 5
            },
            'response': None
        }

        response = self.client.post('/create_scenario',
                                     data=json.dumps(new_scenario),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)

        # Verify scenario was created
        scenario = Scenario.query.filter_by(name='new_test_scenario').first()
        self.assertIsNotNone(scenario)
        self.assertTrue(scenario.community)

    def test_create_scenario_duplicate_name(self):
        """Test creating scenario with duplicate name"""
        self._login()

        duplicate_scenario = {
            'name': 'test_decision',  # Already exists
            'mode': 'Product Development',
            'type': 'informational',
            'text': 'Duplicate scenario',
            'metrics': {
                'staff_retention': 10,
                'partner_retention': 5,
                'partner_growth': 5,
                'tech_debt': 5
            },
            'response': None
        }

        response = self.client.post('/create_scenario',
                                     data=json.dumps(duplicate_scenario),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_set_include_community_scenarios(self):
        """Test /set_include_community_scenarios endpoint"""
        response = self.client.post('/set_include_community_scenarios',
                                     data=json.dumps({'include': True}),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)


if __name__ == '__main__':
    unittest.main()
