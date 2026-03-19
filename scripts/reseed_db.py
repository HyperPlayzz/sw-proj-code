import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
db_file = repo_root / 'database.db'

if db_file.exists():
    db_file.unlink()
    print(f"Deleted existing DB: {db_file}")
else:
    print("No existing DB found, creating new one.")

# Add src to path so we can import the app factory
sys.path.insert(0, str(repo_root / 'src'))

from flask import Flask
from DeskBooker.models import db
from DeskBooker.db import init_db

# Create app without running init_db during app creation
app = Flask(__name__)
app.secret_key = "supersecretkey123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_EXPIRE_ON_COMMIT'] = False
db.init_app(app)

with app.app_context():
    # drop & recreate schema then run idempotent seeder
    print('Dropping and recreating database schema...')
    db.drop_all()
    db.create_all()
    init_db(app)

    # print counts to verify
    from DeskBooker.models import Role, Site, User, Desk, Booking
    print('Seed counts:')
    print('Roles:', Role.query.count())
    print('Sites:', Site.query.count())
    print('Users:', User.query.count())
    print('Desks:', Desk.query.count())
    print('Bookings:', Booking.query.count())

print('Reseed complete.')