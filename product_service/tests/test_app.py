import json
from app import app


def setup_module():
    app.testing = True


def test_home():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200

    data = json.loads(response.data)

    assert data["service"] == "ecommerce-microservice"
    assert data["status"] == "running"


def test_products():
    client = app.test_client()

    response = client.get("/products")

    assert response.status_code == 200

    data = json.loads(response.data)

    assert isinstance(data, list)
    assert len(data) > 0

    assert "id" in data[0]
    assert "name" in data[0]
    assert "price" in data[0]


def test_cart():
    client = app.test_client()

    response = client.get("/cart")

    assert response.status_code == 200

    data = json.loads(response.data)

    assert isinstance(data, list)


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = json.loads(response.data)

    assert data["status"] == "UP"
