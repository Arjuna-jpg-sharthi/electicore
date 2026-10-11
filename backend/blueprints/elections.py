"""Election management and voting endpoints."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..common.authz import current_user, roles_required
from ..common.errors import error
from ..common.parsing import parse_datetime
from ..models import Candidate, Election, Student, Vote, db

bp = Blueprint("elections", __name__, url_prefix="/api")


@bp.get("/elections")
@jwt_required()
def list_elections():
    return jsonify({"elections": [e.to_dict(True) for e in Election.query.order_by(Election.start_date.desc()).all()]})


@bp.post("/elections")
@roles_required("admin")
def create_election():
    data = request.get_json(silent=True) or {}
    title, candidates = str(data.get("title", "")).strip(), data.get("candidates", [])
    if not title or not isinstance(candidates, list) or len(candidates) < 2:
        return error("Title and at least two candidates are required")
    try:
        start, end = parse_datetime(data.get("start_date"), "start_date"), parse_datetime(data.get("end_date"), "end_date")
    except ValueError as exc:
        return error(str(exc))
    if end <= start:
        return error("end_date must be after start_date")
    election = Election(title=title, description=str(data.get("description", "")).strip() or None, start_date=start, end_date=end)
    selected_student_ids = set()
    for item in candidates:
        student_id = item.get("student_id") if isinstance(item, dict) else None
        student = db.session.get(Student, student_id) if student_id else None
        if student_id and not student:
            return error("A selected candidate no longer exists")
        if student and student.id in selected_student_ids:
            return error("A student can only be selected once")
        name = student.name if student else (str(item.get("name", "")).strip() if isinstance(item, dict) else str(item).strip())
        if not name:
            return error("Every candidate needs a name")
        if student:
            selected_student_ids.add(student.id)
        election.candidates.append(Candidate(student_id=student.id if student else None, name=name, manifesto=item.get("manifesto") if isinstance(item, dict) else None))
    db.session.add(election)
    db.session.commit()
    return jsonify({"election": election.to_dict(True)}), 201


@bp.get("/admin/students")
@roles_required("admin")
def list_students_for_admin():
    students = Student.query.order_by(Student.name.asc()).all()
    return jsonify({"students": [{"id": s.id, "name": s.name, "email": s.email} for s in students]})


@bp.post("/elections/<int:election_id>/votes")
@jwt_required()
def cast_vote(election_id):
    election = db.session.get(Election, election_id)
    if not election:
        return error("Election not found", 404)
    if election.to_dict()["status"] != "open":
        return error("Voting is not open for this election", 409)
    candidate_id = (request.get_json(silent=True) or {}).get("candidate_id")
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate or candidate.election_id != election.id:
        return error("Candidate does not belong to this election")
    db.session.add(Vote(election_id=election.id, candidate_id=candidate.id, student_id=current_user().id))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("You have already voted in this election", 409)
    return jsonify({"message": "Vote recorded"}), 201


@bp.get("/elections/<int:election_id>/results")
@roles_required("admin")
def election_results(election_id):
    election = db.session.get(Election, election_id)
    if not election:
        return error("Election not found", 404)
    if election.to_dict()["status"] != "closed":
        return error("Election tallies are available to administrators after voting closes", 409)
    return jsonify(_results_payload(election))


@bp.post("/elections/<int:election_id>/publish-results")
@roles_required("admin")
def publish_election_results(election_id):
    election = db.session.get(Election, election_id)
    if not election:
        return error("Election not found", 404)
    if election.to_dict()["status"] != "closed":
        return error("Results can only be published after voting has closed", 409)
    election.results_published = True
    db.session.commit()
    return jsonify({"message": "Election results published", **_results_payload(election)})


@bp.get("/elections/<int:election_id>/published-results")
def published_election_results(election_id):
    election = db.session.get(Election, election_id)
    if not election:
        return error("Election not found", 404)
    if not election.results_published:
        return error("Results have not been published", 404)
    if election.to_dict()["status"] != "closed":
        return error("Results are not available while voting is open", 409)
    return jsonify(_results_payload(election))


def _results_payload(election):
    counts = dict(db.session.query(Vote.candidate_id, func.count(Vote.id)).filter_by(election_id=election.id).group_by(Vote.candidate_id))
    total_votes = sum(counts.values())
    results = [{**candidate.to_dict(), "votes": counts.get(candidate.id, 0),
                "percentage": round(counts.get(candidate.id, 0) * 100 / total_votes, 1) if total_votes else 0}
               for candidate in election.candidates]
    return {"election": election.to_dict(), "total_votes": total_votes,
            "results_published": election.results_published, "results": results}
