import pytest

from app import create_app, db


@pytest.fixture
def app():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
