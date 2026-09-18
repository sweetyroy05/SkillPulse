import sys
import os

# Add the repo root's backend directory to Python path
# __file__ is api/index.py, so .. is the repo root
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(repo_root, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app

handler = app