import sys
import os

# Ensure the package root (src) is on sys.path so package imports work
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from DeskBooker.main import create_app

app = create_app()

if __name__ == '__main__':
    # Run development server
    app.run(debug=True)