"""Flask extension instances shared by the application factory and blueprints."""

from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from .models import db

jwt = JWTManager()
migrate = Migrate()
