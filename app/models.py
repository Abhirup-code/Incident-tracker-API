from datetime import datetime, timezone

from app import db


def utcnow():
    return datetime.now(timezone.utc)


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False, default="low")
    status = db.Column(db.String(20), nullable=False, default="open")
    service = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    VALID_SEVERITIES = {"low", "medium", "high", "critical"}
    VALID_STATUSES = {"open", "investigating", "resolved"}

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "service": self.service,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
