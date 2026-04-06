import pytest

from app import create_app
from app.extensions import db
from app.models import Brand, Category, Role, User


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin_role = Role(name="Administrador", slug="admin", description="Acesso total")
        customer_role = Role(name="Cliente", slug="customer", description="Cliente")
        db.session.add_all([admin_role, customer_role])
        db.session.flush()

        admin = User(name="Admin", email="admin@example.com", role=admin_role)
        admin.set_password("Admin1234")
        customer = User(name="Cliente", email="cliente@example.com", role=customer_role)
        customer.set_password("Cliente1234")
        db.session.add_all([admin, customer, Category(name="Bicicletas"), Brand(name="Sense")])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
