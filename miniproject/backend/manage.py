"""Small, local-only administration commands for ELECTICORE."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import app
from backend.models import Student, db


def promote(email, role):
    with app.app_context():
        student = Student.query.filter_by(email=email.strip().lower()).first()
        if not student:
            raise SystemExit("No account exists with that email address.")
        student.role = role
        db.session.commit()
        print(f"{student.email} is now a {role}.")


parser = argparse.ArgumentParser(description="ELECTICORE local administration")
subparsers = parser.add_subparsers(dest="command", required=True)
promote_parser = subparsers.add_parser("promote", help="Assign a trusted staff role")
promote_parser.add_argument("email")
promote_parser.add_argument("role", choices=("admin", "committee"))

if __name__ == "__main__":
    args = parser.parse_args()
    if args.command == "promote":
        promote(args.email, args.role)
