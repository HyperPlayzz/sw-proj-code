
## README: How to run the Desk Booking Application

1. Open terminal in project folder:

2. Create and activate venv (optional, you can just open a command line and run step 3):
   python -m venv .venv
   .venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Seed initial data (optional but recommended):
   python scripts/reseed_db.py

5. Run the app:
   python run.py

6. Open browser:
   - `http://127.0.0.1:5000`

## Pages

- `/` - Login / Register
- `/book_desk` - Book a desk
- `/edit_bookings` - Edit existing bookings
- `/delete_bookings` - Delete bookings
- `/lookup_bookings` - Lookup desk availability

## No DB setup required

The app initializes SQLite automatically when started. If you need a clean state, delete `database.db` and restart.

## Access via the Web:
The application is also hosted at https://sw-proj-code.onrender.com/
