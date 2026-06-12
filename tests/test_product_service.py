"""
Unit Tests for Product Catalog Service
======================================
Tests cover all CRUD operations, validation, filtering, and edge cases.
Run with: pytest tests/test_product_service.py -v
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent dirs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product-service'))

from product_service.app import create_app, build_mongo_uri


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """Create test Flask app with mocked MongoDB."""
    app = create_app("testing")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Health Check Tests
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        with patch('flask_pymongo.wrappers.Database.command') as mock_cmd:
            mock_cmd.return_value = {"ok": 1}
            resp = client.get('/health')
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert data['status'] == 'healthy'
            assert data['service'] == 'product-service'


# ---------------------------------------------------------------------------
# Product CRUD Tests
# ---------------------------------------------------------------------------

class TestProductCRUD:
    @patch('product_service.app.mongo')
    def test_create_product(self, mock_mongo, client):
        """Test creating a new product."""
        mock_mongo.db.products.find_one.return_value = None
        mock_mongo.db.products.insert_one.return_value = MagicMock(inserted_id="507f1f77bcf86cd799439011")
        
        resp = client.post('/products', json={
            "name": "Test Product",
            "price": 29.99,
            "sku": "TEST-001",
            "category": "Electronics",
            "stock_quantity": 100
        })
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data['message'] == 'Product created successfully'

    @patch('product_service.app.mongo')
    def test_create_product_duplicate_sku(self, mock_mongo, client):
        """Test creating product with duplicate SKU fails."""
        mock_mongo.db.products.find_one.return_value = {"sku": "TEST-001"}
        
        resp = client.post('/products', json={
            "name": "Test Product",
            "price": 29.99,
            "sku": "TEST-001"
        })
        assert resp.status_code == 409

    @patch('product_service.app.mongo')
    def test_create_product_missing_name(self, mock_mongo, client):
        """Test creating product without name fails validation."""
        resp = client.post('/products', json={"price": 29.99})
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'name is required' in data['error'].lower() or 'required' in data['error'].lower()

    @patch('product_service.app.mongo')
    def test_list_products(self, mock_mongo, client):
        """Test listing all products."""
        mock_mongo.db.products.count_documents.return_value = 2
        mock_mongo.db.products.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
            {"_id": "507f1f77bcf86cd799439011", "name": "Product 1", "price": 10.0, "category": "Test", "sku": "P1"},
            {"_id": "507f1f77bcf86cd799439012", "name": "Product 2", "price": 20.0, "category": "Test", "sku": "P2"}
        ]
        
        resp = client.get('/products')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'products' in data
        assert 'pagination' in data

    @patch('product_service.app.mongo')
    def test_get_product(self, mock_mongo, client):
        """Test getting a single product."""
        mock_mongo.db.products.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "Test Product",
            "price": 29.99,
            "sku": "TEST-001",
            "category": "Electronics",
            "is_active": True
        }
        
        resp = client.get('/products/507f1f77bcf86cd799439011')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['name'] == 'Test Product'

    @patch('product_service.app.mongo')
    def test_get_product_not_found(self, mock_mongo, client):
        """Test getting non-existent product returns 404."""
        mock_mongo.db.products.find_one.return_value = None
        
        resp = client.get('/products/507f1f77bcf86cd799439099')
        assert resp.status_code == 404

    def test_get_product_invalid_id(self, client):
        """Test getting product with invalid ID format."""
        resp = client.get('/products/invalid-id')
        assert resp.status_code == 400

    @patch('product_service.app.mongo')
    def test_update_product(self, mock_mongo, client):
        """Test updating a product."""
        mock_mongo.db.products.update_one.return_value = MagicMock(matched_count=1)
        mock_mongo.db.products.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "Updated Product",
            "price": 39.99,
            "sku": "TEST-001",
            "category": "Electronics",
            "is_active": True
        }
        
        resp = client.put('/products/507f1f77bcf86cd799439011', json={"price": 39.99, "name": "Updated Product"})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['message'] == 'Product updated successfully'

    @patch('product_service.app.mongo')
    def test_delete_product(self, mock_mongo, client):
        """Test soft-deleting a product."""
        mock_mongo.db.products.update_one.return_value = MagicMock(matched_count=1)
        
        resp = client.delete('/products/507f1f77bcf86cd799439011')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['message'] == 'Product deleted successfully'


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------

class TestValidation:
    @patch('product_service.app.mongo')
    def test_negative_price_rejected(self, mock_mongo, client):
        """Test negative price is rejected."""
        resp = client.post('/products', json={"name": "Test", "price": -10})
        assert resp.status_code == 400

    @patch('product_service.app.mongo')
    def test_negative_stock_rejected(self, mock_mongo, client):
        """Test negative stock quantity is rejected."""
        resp = client.post('/products', json={
            "name": "Test", "price": 10, "stock_quantity": -5
        })
        assert resp.status_code == 400

    def test_empty_body_rejected(self, client):
        """Test empty request body is rejected."""
        resp = client.post('/products', json=None)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Helper Function Tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_build_mongo_uri_with_auth(self):
        """Test MongoDB URI builder with credentials."""
        with patch.dict('os.environ', {
            'MONGO_HOST': 'mongodb', 'MONGO_PORT': '27017',
            'MONGO_DB_NAME': 'ecomops', 'MONGO_AUTH_DB': 'admin',
            'MONGO_USERNAME': 'admin', 'MONGO_PASSWORD': 'password123'
        }):
            uri = build_mongo_uri()
            assert 'admin:password123@mongodb:27017/ecomops' in uri

    def test_build_mongo_uri_without_auth(self):
        """Test MongoDB URI builder without credentials."""
        with patch.dict('os.environ', {}, clear=True):
            uri = build_mongo_uri()
            assert uri == 'mongodb://localhost:27017/ecomops'
