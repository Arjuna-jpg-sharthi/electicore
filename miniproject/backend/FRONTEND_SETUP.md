# Frontend setup

The Flask app now serves the portal directly from `../ELECTICORE_frontend/static`; do not copy `index.html` into this directory.

Run `python app.py` from `backend`, then open `http://127.0.0.1:5000`.

Use the profile button in the top-right corner to create an account or sign in. After signing in, elections are loaded from the API, voting is persisted, and confidential safety reports can be submitted and tracked.
