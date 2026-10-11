"""Authentication endpoints."""

import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy.exc import IntegrityError

from ..common.authz import current_user
from ..common.errors import error
from ..models import Student, db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name, email, password = (str(data.get(key, "")).strip() for key in ("name", "email", "password"))
    if not name or not email or not password:
        return error("Name, email and password are required")
    if len(name) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return error("Enter a valid name and email address")
    if len(password) < 10:
        return error("Password must contain at least 10 characters")
    student = Student(name=name, email=email.lower())
    student.set_password(password)
    db.session.add(student)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("Email already registered", 409)
    return jsonify({"message": "Student registered successfully", "student": student.to_dict()}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email, password = str(data.get("email", "")).strip().lower(), str(data.get("password", ""))
    student = Student.query.filter_by(email=email).first()
    if not student or not student.check_password(password):
        return error("Invalid email or password", 401)
    return jsonify({"token": create_access_token(identity=str(student.id)), "student": student.to_dict()})


@bp.get("/me")
@jwt_required()
def me():
    student = current_user()
    return jsonify({"student": student.to_dict()}) if student else error("Student not found", 404)


@bp.patch("/me")
@jwt_required()
def update_me():
    student = current_user()
    if not student:
        return error("Student not found", 404)

    data = request.get_json(silent=True) or {}
    changed = False

    if "name" in data:
        name = str(data.get("name", "")).strip()
        if not name or len(name) > 100:
            return error("Name must contain between 1 and 100 characters")
        student.name = name
        changed = True

    if "email" in data:
        email = str(data.get("email", "")).strip().lower()
        if len(email) > 120 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return error("Enter a valid email address")
        existing = Student.query.filter(Student.email == email, Student.id != student.id).first()
        if existing:
            return error("Email already registered", 409)
        student.email = email
        changed = True

    if "new_password" in data:
        current_password = str(data.get("current_password", ""))
        new_password = str(data.get("new_password", ""))
        if not student.check_password(current_password):
            return error("Current password is incorrect", 401)
        if len(new_password) < 10:
            return error("New password must contain at least 10 characters")
        student.set_password(new_password)
        changed = True

    if not changed:
        return error("Enter a profile change or a new password")

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("Email already registered", 409)
    return jsonify({"message": "Profile updated successfully", "student": student.to_dict()})
