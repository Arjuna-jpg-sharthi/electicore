"""Backward-compatible application entry point for development and WSGI servers."""

import os
import sys
from pathlib import Path

# Make both `python -m backend.app` and `python backend/app.py` use one package
# namespace, preventing duplicate SQLAlchemy model registries.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.application import create_app

app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
