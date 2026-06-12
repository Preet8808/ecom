"""
Unit Tests for Shopping Cart Service
====================================
Tests cover cart creation, item management, coupons, and checkout.
Run with: pytest tests/test_cart_service.py -v
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cart-service'))

from cart_service.app import create_app, calculate_cart_totals


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """Create test Flask app."""
    app = create_app("testing")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Cart Creation Tests
# ---------------------------------------------------------------------------

class TestCartCreation:
    @patch('cart_service.app.mongo')
    def test_create_cart(self, mock_mongo, client):
        """Test creating a new cart."""
        mock_insert = MagicMock()
        mock_insert.inserted_id = "507f1f77bcf86cd799439011"
        mock_mongo.db.carts.insert_one.return_value = mock_insert
        
        resp = client.post('/carts', json={"user_id": "test_user"})
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data['message'] == 'Cart created successfully'
        assert 'cart' in data

    @patch('cart_service.app.mongo')
    def test_create_cart_default_user(self, mock_mongo, client):
        """Test creating a cart with default guest user."""
        mock_insert = MagicMock()
        mock_insert.inserted_id = "507f1f77bcf86cd799439011"
        mock_mongo.db.carts.insert_one.return_value = mock_insert
        
        resp = client.post('/carts', json={})
        assert resp.status_code == 201

    @patch('cart_service.app.mongo')
    def test_get_cart(self, mock_mongo, client):
        """Test retrieving a cart."""
        mock_mongo.db.carts.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": "test",
            "items": [
                {"sku": "PROD-1", "name": "Widget", "price": 10.0, "quantity": 2}
            ],
            "subtotal": 20.0,
            "total": 21.60,
            "status": "active"
        }
        
        resp = client.get('/carts/507f1f77bcf86cd799439011')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['item_count'] == 2

    @patch('cart_service.app.mongo')
    def test_get_cart_not_found(self, mock_mongo, client):
        """Test getting non-existent cart returns 404."""
        mock_mongo.db.carts.find_one.return_value = None
        resp = client.get('/carts/507f1f77bcf86cd799439099')
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Cart Item Tests
# ---------------------------------------------------------------------------

class TestCartItems:
    @patch('cart_service.app.mongo')
    def test_add_item(self, mock_mongo, client):
        """Test adding item to cart."""
        mock_mongo.db.carts.find_one.side_effect = [
            {"_id": "507f1f77bcf86cd799439011", "items": [], "discount_code": "", "shipping_method": "standard"},
            {"_id": "507f1f77bcf86cd799439011", "items": [
                {"sku": "PROD-1", "name": "Widget", "price": 10.0, "quantity": 2}
            ], "discount_code": "", "shipping_method": "standard"}
        ]
        
        resp = client.post('/carts/507f1f77bcf86cd799439011/items', json={
            "sku": "PROD-1", "name": "Widget", "price": 10.0, "quantity": 2
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['message'] == 'Item added to cart'

    @patch('cart_service.app.mongo')
    def test_add_item_missing_sku(self, mock_mongo, client):
        """Test adding item without SKU fails."""
        resp = client.post('/carts/507f1f77bcf86cd799439011/items', json={
            "quantity": 1
        })
        assert resp.status_code == 400
        assert 'sku' in json.loads(resp.data)['error'].lower()

    @patch('cart_service.app.mongo')
    def test_remove_item(self, mock_mongo, client):
        """Test removing item from cart."""
        mock_mongo.db.carts.find_one.side_effect = [
            {"_id": "507f1f77bcf86cd799439011", "items": [
                {"sku": "PROD-1", "name": "Widget", "price": 10.0, "quantity": 1}
            ], "discount_code": "", "shipping_method": "standard"},
            {"_id": "507f1f77bcf86cd799439011", "items": [], "discount_code": "", "shipping_method": "standard"}
        ]
        
        resp = client.delete('/carts/507f1f77bcf86cd799439011/items/PROD-1')
        assert resp.status_code == 200

    @patch('cart_service.app.mongo')
    def test_update_item_quantity(self, mock_mongo, client):
        """Test updating item quantity."""
        mock_mongo.db.carts.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "items": [{"sku": "PROD-1", "name": "Widget", "price": 10.0, "quantity": 1}],
            "discount_code": "",
            "shipping_method": "standard"
        }
        
        resp = client.put('/carts/507f1f77bcf86cd799439011/items/PROD-1', json={"quantity": 5})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['message'] == 'Item quantity updated'


# ---------------------------------------------------------------------------
# Coupon Tests
# ---------------------------------------------------------------------------

class TestCoupons:
    @patch('cart_service.app.mongo')
    def test_apply_valid_coupon(self, mock_mongo, client):
        """Test applying a valid discount coupon."""
        mock_mongo.db.carts.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "items": [{"sku": "PROD-1", "name": "Widget", "price": 100.0, "quantity": 1}],
            "discount_code": "",
            "shipping_method": "standard"
        }
        
        resp = client.post('/carts/507f1f77bcf86cd799439011/apply-coupon', json={"code": "SAVE10"})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'coupon_details' in data
        assert data['message'] == "Coupon 'SAVE10' applied successfully"

    @patch('cart_service.app.mongo')
    def test_apply_invalid_coupon(self, mock_mongo, client):
        """Test applying invalid coupon fails."""
        mock_mongo.db.carts.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "items": [],
            "discount_code": ""
        }
        
        resp = client.post('/carts/507f1f77bcf86cd799439011/apply-coupon', json={"code": "INVALID"})
        assert resp.status_code == 400

    @patch('cart_service.app.mongo')
    def test_list_coupons(self, mock_mongo, client):
        """Test listing all available coupons."""
        resp = client.get('/coupons')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'coupons' in data
        assert len(data['coupons']) > 0
        coupon_codes = [c['code'] for c in data['coupons']]
        assert 'SAVE10' in coupon_codes


# ---------------------------------------------------------------------------
# Checkout Tests
# ---------------------------------------------------------------------------

class TestCheckout:
    @patch('cart_service.app.mongo')
    def test_checkout_empty_cart_fails(self, mock_mongo, client):
        """Test checkout with empty cart fails."""
        mock_mongo.db.carts.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "items": [],
            "discount_code": "",
            "shipping_method": "standard"
        }
        
        resp = client.post('/carts/507f1f77bcf86cd799439011/checkout', json={})
        assert resp.status_code == 400
        assert 'empty' in json.loads(resp.data)['error'].lower()

    @patch('cart_service.app.mongo')
    def test_checkout_success(self, mock_mongo, client):
        """Test successful checkout."""
        mock_mongo.db.carts.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": "test",
            "items": [{"sku": "PROD-1", "name": "Widget", "price": 50.0, "quantity": 2}],
            "discount_code": "",
            "shipping_method": "standard"
        }
        
        resp = client.post('/carts/507f1f77bcf86cd799439011/checkout', json={
            "payment_method": "credit_card",
            "shipping_address": {"street": "123 Test St", "city": "Test City"}
        })
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data['message'] == 'Order placed successfully'
        assert 'order' in data
        assert data['order']['status'] == 'confirmed'


# ---------------------------------------------------------------------------
# Calculation Helper Tests
# ---------------------------------------------------------------------------

class TestCalculations:
    def test_cart_totals_basic(self):
        """Test basic cart total calculation."""
        items = [
            {"price": 10.0, "quantity": 2},
            {"price": 25.0, "quantity": 1}
        ]
        totals = calculate_cart_totals(items)
        assert totals['subtotal'] == 45.0
        assert totals['tax'] == 3.6  # 8% of 45
        assert totals['shipping'] == 5.99  # Under free threshold

    def test_cart_totals_with_discount(self):
        """Test cart totals with percentage discount."""
        items = [
            {"price": 100.0, "quantity": 1}
        ]
        totals = calculate_cart_totals(items, discount_code="SAVE10")
        assert totals['discount'] == 10.0  # 10% of 100
        assert totals['subtotal'] == 100.0
        assert totals['tax'] == 7.2  # 8% of (100 - 10)

    def test_cart_totals_free_shipping(self):
        """Test free shipping over threshold."""
        items = [
            {"price": 80.0, "quantity": 1}
        ]
        totals = calculate_cart_totals(items)
        assert totals['shipping'] == 0.0  # Over $75 threshold

    def test_cart_totals_express_shipping(self):
        """Test express shipping cost."""
        items = [
            {"price": 80.0, "quantity": 1}
        ]
        totals = calculate_cart_totals(items, shipping_method="express")
        assert totals['shipping'] == 12.99  # Express is always charged

    def test_cart_totals_empty(self):
        """Test empty cart totals."""
        totals = calculate_cart_totals([])
        assert totals['subtotal'] == 0.0
        assert totals['total'] == 0.0
        assert totals['shipping'] == 0.0
