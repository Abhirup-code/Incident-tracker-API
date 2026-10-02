from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app import db
from app.models import Incident

bp = Blueprint("incidents", __name__)


@bp.route("/healthz", methods=["GET"])
def health_check():
    """Liveness/readiness probe target for Kubernetes."""
    return jsonify({"status": "ok"}), 200


@bp.route("/incidents", methods=["POST"])
def create_incident():
    data = request.get_json(silent=True) or {}

    title = data.get("title")
    service = data.get("service")
    if not title or not service:
        return jsonify({"error": "title and service are required"}), 400

    severity = data.get("severity", "low")
    if severity not in Incident.VALID_SEVERITIES:
        return jsonify({"error": f"severity must be one of {sorted(Incident.VALID_SEVERITIES)}"}), 400

    incident = Incident(
        title=title,
        description=data.get("description"),
        severity=severity,
        service=service,
        status="open",
    )
    db.session.add(incident)
    db.session.commit()

    return jsonify(incident.to_dict()), 201


@bp.route("/incidents", methods=["GET"])
def list_incidents():
    query = Incident.query

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    severity = request.args.get("severity")
    if severity:
        query = query.filter_by(severity=severity)

    service = request.args.get("service")
    if service:
        query = query.filter_by(service=service)

    incidents = query.order_by(Incident.created_at.desc()).all()
    return jsonify([i.to_dict() for i in incidents]), 200


@bp.route("/incidents/<int:incident_id>", methods=["GET"])
def get_incident(incident_id):
    incident = db.session.get(Incident, incident_id)
    if not incident:
        return jsonify({"error": "incident not found"}), 404
    return jsonify(incident.to_dict()), 200


@bp.route("/incidents/<int:incident_id>", methods=["PATCH"])
def update_incident(incident_id):
    incident = db.session.get(Incident, incident_id)
    if not incident:
        return jsonify({"error": "incident not found"}), 404

    data = request.get_json(silent=True) or {}

    if "status" in data:
        if data["status"] not in Incident.VALID_STATUSES:
            return jsonify({"error": f"status must be one of {sorted(Incident.VALID_STATUSES)}"}), 400
        incident.status = data["status"]
        if data["status"] == "resolved" and incident.resolved_at is None:
            incident.resolved_at = datetime.now(timezone.utc)
        elif data["status"] != "resolved":
            incident.resolved_at = None

    if "severity" in data:
        if data["severity"] not in Incident.VALID_SEVERITIES:
            return jsonify({"error": f"severity must be one of {sorted(Incident.VALID_SEVERITIES)}"}), 400
        incident.severity = data["severity"]

    if "description" in data:
        incident.description = data["description"]

    db.session.commit()
    return jsonify(incident.to_dict()), 200


@bp.route("/incidents/<int:incident_id>", methods=["DELETE"])
def delete_incident(incident_id):
    incident = db.session.get(Incident, incident_id)
    if not incident:
        return jsonify({"error": "incident not found"}), 404

    db.session.delete(incident)
    db.session.commit()
    return "", 204


@bp.route("/incidents/stats", methods=["GET"])
def incident_stats():
    """Basic metrics endpoint: counts by status and severity."""
    total = Incident.query.count()
    by_status = {}
    for status in Incident.VALID_STATUSES:
        by_status[status] = Incident.query.filter_by(status=status).count()

    by_severity = {}
    for severity in Incident.VALID_SEVERITIES:
        by_severity[severity] = Incident.query.filter_by(severity=severity).count()

    return jsonify({"total": total, "by_status": by_status, "by_severity": by_severity}), 200
