"""Student notification endpoints."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..common.authz import current_user, roles_required
from ..common.errors import error
from ..models import Notification, Student, db

bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@bp.get("")
@jwt_required()
def notifications():
    user = current_user()
    items = Notification.query.filter_by(student_id=user.id).order_by(Notification.created_at.desc()).all()
    return jsonify({"notifications": [notification.to_dict() for notification in items]})


@bp.patch("/<int:notification_id>/read")
@jwt_required()
def mark_read(notification_id):
    user = current_user()
    item = db.session.get(Notification, notification_id)
    if not item or item.student_id != user.id:
        return error("Notification not found", 404)
    item.is_read = True
    db.session.commit()
    return jsonify({"notification": item.to_dict()})


@bp.post("/read-all")
@jwt_required()
def mark_all_read():
    user = current_user()
    updated = Notification.query.filter_by(student_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"updated": updated})


@bp.post("")
@roles_required("admin", "committee")
def create_notification():
    data = request.get_json(silent=True) or {}
    title, message, student_id = str(data.get("title", "")).strip(), str(data.get("message", "")).strip(), data.get("student_id")
    if not title or not message or not db.session.get(Student, student_id):
        return error("title, message and a valid student_id are required")
    notification = Notification(student_id=student_id, title=title, message=message)
    db.session.add(notification)
    db.session.commit()
    return jsonify({"notification": notification.to_dict()}), 201
