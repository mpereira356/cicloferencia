from app.extensions import db
from app.models import Brand, Category, Product, User


def login(client, email, password):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=False)


def test_login_validation_rejects_invalid_password(client):
    response = login(client, "admin@example.com", "senha-errada")
    assert response.status_code == 401


def test_protected_route_redirects_when_not_authenticated(client):
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_admin_permission_blocks_customer(client):
    login(client, "cliente@example.com", "Cliente1234")
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 302


def test_admin_can_create_product(client, app):
    login(client, "admin@example.com", "Admin1234")
    with app.app_context():
        category = Category.query.first()
        brand = Brand.query.first()

    response = client.post(
        "/admin/produtos/novo",
        data={
            "name": "Bike Teste",
            "sku": "TEST-001",
            "short_description": "Resumo",
            "description": "Descrição longa",
            "technical_specs": "Spec",
            "price": "1000.00",
            "promotional_price": "900.00",
            "stock": "2",
            "category_id": category.id,
            "subcategory_id": 0,
            "brand_id": brand.id,
            "is_featured": "y",
            "is_bike": "y",
            "is_active": "y",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        assert Product.query.filter_by(sku="TEST-001").first() is not None


def test_register_creates_user(client, app):
    response = client.post(
        "/auth/cadastro",
        data={
            "name": "Novo Cliente",
            "email": "novo@example.com",
            "phone": "11999999999",
            "password": "Senha1234",
            "confirm_password": "Senha1234",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        assert User.query.filter_by(email="novo@example.com").first() is not None
