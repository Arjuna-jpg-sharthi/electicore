"""Campus events and study-resource endpoints."""

import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from ..common.authz import current_user, roles_required
from ..common.errors import error
from ..common.parsing import parse_datetime
from ..models import DoubtPost, Event, Resource, db

bp = Blueprint("events", __name__, url_prefix="/api")
ALLOWED_RESOURCE_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "zip"}


@bp.get("/events")
def list_events():
    return jsonify({"events": [event.to_dict() for event in Event.query.order_by(Event.starts_at).all()]})


@bp.post("/events")
@roles_required("admin")
def create_event():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return error("Event name is required")
    try:
        starts_at = parse_datetime(data.get("starts_at"), "starts_at")
    except ValueError as exc:
        return error(str(exc))
    event = Event(name=name, event_type=str(data.get("type", "Event")).strip(), description=str(data.get("description", "")).strip() or None, venue=str(data.get("venue", "")).strip() or None, starts_at=starts_at)
    db.session.add(event)
    db.session.commit()
    return jsonify({"event": event.to_dict()}), 201


@bp.get("/resources")
def list_resources():
    resources = Resource.query.order_by(Resource.created_at.desc()).all()
    return jsonify({"resources": [resource.to_dict() for resource in resources]})


@bp.post("/resources")
@jwt_required()
def upload_resource():
    title = str(request.form.get("title", "")).strip()
    subject = str(request.form.get("subject", "")).strip()
    description = str(request.form.get("description", "")).strip() or None
    uploaded_file = request.files.get("file")
    if not title or not subject or not uploaded_file or not uploaded_file.filename:
        return error("Title, subject and a resource file are required")
    original_filename = secure_filename(uploaded_file.filename)
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if not original_filename or extension not in ALLOWED_RESOURCE_EXTENSIONS:
        return error("Allowed files: PDF, DOC, DOCX, PPT, PPTX, TXT and ZIP")
    stored_filename = f"{uuid.uuid4().hex}.{extension}"
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    uploaded_file.save(upload_dir / stored_filename)
    resource = Resource(title=title[:150], subject=subject[:100], description=description,
                        original_filename=original_filename, stored_filename=stored_filename,
                        mime_type=uploaded_file.mimetype, uploaded_by_id=current_user().id)
    db.session.add(resource)
    db.session.commit()
    return jsonify({"resource": resource.to_dict()}), 201


@bp.get("/resources/<int:resource_id>/download")
def download_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if not resource:
        return error("Resource not found", 404)
    return send_from_directory(current_app.config["UPLOAD_DIR"], resource.stored_filename,
                               as_attachment=True, download_name=resource.original_filename)


@bp.delete("/resources/<int:resource_id>")
@roles_required("admin")
def delete_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if not resource:
        return error("Resource not found", 404)

    upload_dir = Path(current_app.config["UPLOAD_DIR"]).resolve()
    stored_path = (upload_dir / resource.stored_filename).resolve()
    if stored_path.parent != upload_dir:
        return error("Invalid resource file path", 400)

    db.session.delete(resource)
    db.session.commit()
    stored_path.unlink(missing_ok=True)
    return jsonify({"message": "Study resource deleted"})


ALLOWED_AUDIO_TYPES = {
    "audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a",
    "audio/mpeg": "mp3", "audio/wav": "wav", "audio/x-wav": "wav",
}
MAX_DOUBT_AUDIO_BYTES = 5 * 1024 * 1024


@bp.get("/doubts")
@jwt_required()
def list_doubts():
    questions = (DoubtPost.query.filter_by(parent_id=None)
                 .order_by(DoubtPost.created_at.desc()).limit(100).all())
    return jsonify({"questions": [question.to_dict(include_replies=True) for question in questions]})


@bp.post("/doubts")
@jwt_required()
def create_doubt_post():
    title = str(request.form.get("title", "")).strip()
    body = str(request.form.get("body", "")).strip()
    parent_id = request.form.get("parent_id", "").strip()
    audio = request.files.get("audio")
    if len(body) > 3000:
        return error("Messages can be up to 3,000 characters.")
    if not parent_id and (not title or len(title) > 160):
        return error("A question title of up to 160 characters is required.")
    parent = None
    if parent_id:
        try:
            parent = db.session.get(DoubtPost, int(parent_id))
        except (TypeError, ValueError):
            parent = None
        if not parent or parent.parent_id is not None:
            return error("This question is no longer available for replies.", 404)
    if not body and not audio and parent:
        return error("Add a written message or a voice recording.")

    audio_filename = None
    audio_mime_type = None
    if audio and audio.filename:
        mime_type = (audio.mimetype or "").lower().split(";", 1)[0].strip()
        extension = ALLOWED_AUDIO_TYPES.get(mime_type)
        if not extension:
            return error("Use a WebM, OGG, MP4, MP3, or WAV voice recording.")
        content = audio.stream.read(MAX_DOUBT_AUDIO_BYTES + 1)
        if len(content) > MAX_DOUBT_AUDIO_BYTES:
            return error("Voice recordings must be smaller than 5 MB.", 413)
        audio_filename = f"{uuid.uuid4().hex}.{extension}"
        audio_mime_type = mime_type
        audio_dir = Path(current_app.config["UPLOAD_DIR"]) / "doubt-audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        (audio_dir / audio_filename).write_bytes(content)

    post = DoubtPost(student_id=current_user().id, parent=parent,
                     title=title[:160] if not parent else None,
                     body=body or None, audio_filename=audio_filename,
                     audio_mime_type=audio_mime_type)
    db.session.add(post)
    db.session.commit()
    return jsonify({"post": post.to_dict()}), 201


@bp.get("/doubts/<int:post_id>/audio")
@jwt_required()
def get_doubt_audio(post_id):
    post = db.session.get(DoubtPost, post_id)
    if not post or not post.audio_filename:
        return error("Voice recording not found.", 404)
    audio_dir = Path(current_app.config["UPLOAD_DIR"]) / "doubt-audio"
    return send_from_directory(audio_dir, post.audio_filename, mimetype=post.audio_mime_type,
                               as_attachment=False, conditional=True)
