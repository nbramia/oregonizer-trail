from app import app, db, User
from werkzeug.security import generate_password_hash

# Set up the application context
with app.app_context():
    # Create the database tables
    db.create_all()

    # Create a test user if it doesn't already exist
    username = 'test'
    password = 'test'
    user = User.query.filter_by(username=username).first()
    if user is None:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print('User created successfully.')
    else:
        print('User already exists.')
