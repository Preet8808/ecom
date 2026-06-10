from app import app

client = app.test_client()

def test_home():
    response = client.get("/")
    assert response.status_code == 200

def test_products():
    response = client.get("/products")
    assert response.status_code == 200
