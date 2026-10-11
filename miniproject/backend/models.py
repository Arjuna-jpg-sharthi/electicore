from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email,
                "role": self.role, "created_at": self.created_at.isoformat()}


class Election(db.Model):
    __tablename__ = "elections"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    results_published = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    candidates = db.relationship("Candidate", backref="election", cascade="all, delete-orphan", lazy=True)

    def to_dict(self, include_candidates=False):
        # Datetimes entered in the dashboard are campus-local times.
        now = datetime.now()
        status = "upcoming" if now < self.start_date else "closed" if now > self.end_date else "open"
        data = {"id": self.id, "title": self.title, "description": self.description,
                "start_date": self.start_date.isoformat(), "end_date": self.end_date.isoformat(),
                "status": status, "results_published": self.results_published}
        if include_candidates:
            data["candidates"] = [candidate.to_dict() for candidate in self.candidates]
        return data


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    manifesto = db.Column(db.Text)

    def to_dict(self):
        return {"id": self.id, "student_id": self.student_id, "name": self.name, "manifesto": self.manifesto}


class Vote(db.Model):
    __tablename__ = "votes"
    __table_args__ = (db.UniqueConstraint("election_id", "student_id", name="one_vote_per_student"),)

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    cast_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class SafetyReport(db.Model):
    __tablename__ = "safety_reports"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    incident = db.Column(db.Text, nullable=False)
    incident_date = db.Column(db.Date)
    incident_time = db.Column(db.String(20))
    location = db.Column(db.String(200))
    people_involved = db.Column(db.Text)
    additional_details = db.Column(db.Text)
    ai_drafting_consent = db.Column(db.Boolean, nullable=False, default=False)
    ai_severity = db.Column(db.String(20), nullable=False, default="unassessed")
    ai_assessment_note = db.Column(db.String(500))
    status = db.Column(db.String(30), nullable=False, default="submitted")
    ai_draft = db.Column(db.Text)
    recipient_email = db.Column(db.String(255))
    delivery_status = db.Column(db.String(40), nullable=False, default="pending_configuration")
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    student = db.relationship("Student")

    def to_dict(self, include_identity=False):
        data = {"id": self.id, "incident": self.incident, "incident_date": self.incident_date.isoformat() if self.incident_date else None,
                "incident_time": self.incident_time, "location": self.location,
                "people_involved": self.people_involved, "additional_details": self.additional_details,
                "ai_drafting_consent": self.ai_drafting_consent,
                "ai_severity": self.ai_severity, "ai_assessment_note": self.ai_assessment_note,
                "status": self.status, "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(), "ai_draft": self.ai_draft,
                "recipient_email": self.recipient_email, "delivery_status": self.delivery_status,
                "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None}
        if include_identity:
            data["student"] = self.student.to_dict()
        return data


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    event_type = db.Column(db.String(50), nullable=False, default="Event")
    description = db.Column(db.Text)
    venue = db.Column(db.String(150))
    starts_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "type": self.event_type,
                "description": self.description, "venue": self.venue,
                "starts_at": self.starts_at.isoformat()}


class Resource(db.Model):
    """A study resource uploaded by an authenticated campus user."""
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    mime_type = db.Column(db.String(100))
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    uploaded_by = db.relationship("Student")

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "subject": self.subject,
            "description": self.description, "filename": self.original_filename,
            "mime_type": self.mime_type, "created_at": self.created_at.isoformat(),
            "uploaded_by": self.uploaded_by.name if self.uploaded_by else "Campus member",
            "download_url": f"/api/resources/{self.id}/download",
        }


class DoubtPost(db.Model):
    """A student question or reply in the campus doubt discussion board."""
    __tablename__ = "doubt_posts"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("doubt_posts.id"), nullable=True, index=True)
    title = db.Column(db.String(160))
    body = db.Column(db.Text)
    audio_filename = db.Column(db.String(100))
    audio_mime_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    student = db.relationship("Student")
    parent = db.relationship("DoubtPost", remote_side=[id], back_populates="replies")
    replies = db.relationship("DoubtPost", back_populates="parent", cascade="all, delete-orphan",
                              order_by="DoubtPost.created_at")

    def to_dict(self, include_replies=False):
        result = {
            "id": self.id, "parent_id": self.parent_id, "title": self.title, "body": self.body,
            "student": self.student.name if self.student else "Campus student",
            "created_at": self.created_at.isoformat(),
            "audio_url": f"/api/doubts/{self.id}/audio" if self.audio_filename else None,
        }
        if include_replies:
            result["replies"] = [reply.to_dict() for reply in self.replies]
        return result


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "message": self.message,
                "is_read": self.is_read, "created_at": self.created_at.isoformat()}
