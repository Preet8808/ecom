"""
Shopping Cart Service - EcomOps Platform
========================================
Handles shopping cart operations: create cart, add items, update quantities,
remove items, apply discounts, and checkout. Integrated with MongoDB and
communicates with Product Service for price validation.

API Endpoints:
  GET    /health            - Health check
  GET    /metrics           - Prometheus metrics
  POST   /carts             - Create a new cart
  GET    /carts/<id>        - Get cart contents
  POST   /carts/<id>/items  - Add item to cart
  PUT    /carts/<id>/items/<sku>  - Update item quantity
  DELETE /carts/<id>/items/<sku>  - Remove item from cart
  POST   /carts/<id>/apply-coupon   - Apply discount coupon
  POST   /carts/<id>/checkout       - Process checkout
  DELETE /carts/<id>        - Delete cart
"""

from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson import ObjectId
from datetime import datetime, timedelta
import os
import requests

# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------

def create_app(config_name="production"):
    app = Flask(__name__)
    
    app.config["MONGO_URI"] = build_mongo_uri()
    app.config["JSON_SORT_KEYS"] = False
    
    mongo = PyMongo(app)
    app.mongo = mongo
    app.start_time = datetime.utcnow()
    
    # Product service URL for price validation
    app.product_service_url = os.environ.get(
        "PRODUCT_SERVICE_URL",
        "http://product-service.ecomops.svc.cluster.local:5000"
    )
    
    return app


def build_mongo_uri():
    """Build MongoDB connection URI from environment variables."""
    host = os.environ.get("MONGO_HOST", "localhost")
    port = os.environ.get("MONGO_PORT", "27017")
    db = os.environ.get("MONGO_DB_NAME", "ecomops")
    auth_db = os.environ.get("MONGO_AUTH_DB", "admin")
    username = os.environ.get("MONGO_USERNAME", "")
    password = os.environ.get("MONGO_PASSWORD", "")
    
    if username and password:
        return f"mongodb://{username}:{password}@{host}:{port}/{db}?authSource={auth_db}"
    return f"mongodb://{host}:{port}/{db}"


# ---------------------------------------------------------------------------
# Initialize
# ---------------------------------------------------------------------------

app = create_app()
mongo = app.mongo


# ---------------------------------------------------------------------------
# Predefined Coupons for Business Logic
# ---------------------------------------------------------------------------

COUPONS = {
    "SAVE10": {"type": "percentage", "value": 10, "min_order": 50.0, "description": "10% off on orders above $50"},
    "SAVE20": {"type": "percentage", "value": 20, "min_order": 100.0, "description": "20% off on orders above $100"},
    "WELCOME5": {"type": "fixed", "value": 5.0, "min_order": 25.0, "description": "$5 off on first order above $25"},
    "FREESHIP": {"type": "shipping", "value": 0, "min_order": 75.0, "description": "Free shipping on orders above $75"},
    "FLASH25": {"type": "percentage", "value": 25, "min_order": 150.0, "description": "25% flash sale - orders above $150"},
}

SHIPPING_RATES = {
    "standard": 5.99,
    "express": 12.99,
    "free_threshold": 75.0
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def serialize_cart(cart):
    """Convert MongoDB cart document to JSON-serializable dict."""
    return {
        "id": str(cart["_id"]),
        "user_id": cart.get("user_id", ""),
        "items": cart.get("items", []),
        "subtotal": round(cart.get("subtotal", 0.0), 2),
        "discount": round(cart.get("discount", 0.0), 2),
        "discount_code": cart.get("discount_code", ""),
        "shipping": round(cart.get("shipping", 0.0), 2),
        "shipping_method": cart.get("shipping_method", "standard"),
        "tax": round(cart.get("tax", 0.0), 2),
        "total": round(cart.get("total", 0.0), 2),
        "item_count": sum(item.get("quantity", 0) for item in cart.get("items", [])),
        "status": cart.get("status", "active"),
        "created_at": cart.get("created_at", datetime.utcnow()).isoformat() if isinstance(cart.get("created_at"), datetime) else cart.get("created_at"),
        "updated_at": cart.get("updated_at", datetime.utcnow()).isoformat() if isinstance(cart.get("updated_at"), datetime) else cart.get("updated_at"),
        "expires_at": cart.get("expires_at", datetime.utcnow()).isoformat() if isinstance(cart.get("expires_at"), datetime) else cart.get("expires_at"),
    }


def calculate_cart_totals(items, discount_code=None, shipping_method="standard"):
    """Calculate subtotal, tax, shipping, discount, and total for a cart."""
    subtotal = sum(item.get("price", 0) * item.get("quantity", 0) for item in items)
    
    # Calculate discount
    discount = 0.0
    if discount_code and discount_code in COUPONS:
        coupon = COUPONS[discount_code]
        if subtotal >= coupon["min_order"]:
            if coupon["type"] == "percentage":
                discount = subtotal * (coupon["value"] / 100)
            elif coupon["type"] == "fixed":
                discount = min(coupon["value"], subtotal)
    
    # Calculate shipping
    shipping = 0.0
    if shipping_method == "express":
        shipping = SHIPPING_RATES["express"]
    elif subtotal < SHIPPING_RATES["free_threshold"]:
        shipping = SHIPPING_RATES["standard"]
    
    # Tax (8%)
    taxable_amount = max(0, subtotal - discount)
    tax = taxable_amount * 0.08
    
    # Total
    total = taxable_amount + tax + shipping
    
    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping": round(shipping, 2),
        "tax": round(tax, 2),
        "total": round(total, 2)
    }


def validate_product_with_service(sku):
    """Validate product exists and get current price from Product Service."""
    try:
        resp = requests.get(
            f"{app.product_service_url}/products",
            params={"search": sku},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            for product in data.get("products", []):
                if product["sku"] == sku and product.get("is_active", True):
                    return True, product["price"], product["name"]
        return False, 0.0, ""
    except requests.RequestException:
        # If product service is unavailable, allow add (optimistic)
        return True, 0.0, ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Kubernetes probes."""
    try:
        mongo.db.command("ping")
        uptime = (datetime.utcnow() - app.start_time).total_seconds()
        return jsonify({
            "status": "healthy",
            "service": "cart-service",
            "version": "1.0.0",
            "uptime_seconds": round(uptime, 2),
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "cart-service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503


@app.route("/carts", methods=["POST"])
def create_cart():
    """Create a new shopping cart."""
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id", "guest")
        
        cart_doc = {
            "user_id": user_id,
            "items": [],
            "subtotal": 0.0,
            "discount": 0.0,
            "discount_code": "",
            "shipping": 0.0,
            "shipping_method": "standard",
            "tax": 0.0,
            "total": 0.0,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=48),
        }
        
        result = mongo.db.carts.insert_one(cart_doc)
        cart_doc["_id"] = result.inserted_id
        
        return jsonify({
            "message": "Cart created successfully",
            "cart": serialize_cart(cart_doc)
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/carts/<cart_id>", methods=["GET"])
def get_cart(cart_id):
    """Get cart by ID with full item details."""
    try:
        if not ObjectId.is_valid(cart_id):
            return jsonify({"error": "Invalid cart ID format"}), 400
        
        cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        if not cart:
            return jsonify({"error": "Cart not found"}), 404
        
        # Recalculate totals to ensure accuracy
        totals = calculate_cart_totals(
            cart.get("items", []),
            cart.get("discount_code"),
            cart.get("shipping_method", "standard")
        )
        cart.update(totals)
        
        # Update cart with recalculated values
        mongo.db.carts.update_one(
            {"_id": ObjectId(cart_id)},
            {"$set": {**totals, "updated_at": datetime.utcnow()}}
        )
        
        return jsonify(serialize_cart(cart)), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/carts/<cart_id>/items", methods=["POST"])
def add_item(cart_id):
    """Add an item to the cart."""
    try:
        if not ObjectId.is_valid(cart_id):
            return jsonify({"error": "Invalid cart ID format"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        sku = data.get("sku")
        quantity = int(data.get("quantity", 1))
        
        if not sku:
            return jsonify({"error": "Product SKU is required"}), 400
        if quantity < 1:
            return jsonify({"error": "Quantity must be at least 1"}), 400
        
        # Find cart
        cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        if not cart:
            return jsonify({"error": "Cart not found"}), 404
        
        # Validate product and get price
        is_valid, price, product_name = validate_product_with_service(sku)
        if not is_valid and price == 0.0:
            return jsonify({"error": f"Product with SKU '{sku}' not found"}), 404
        
        # Use provided price if available, else from product service
        item_price = data.get("price", price) if data.get("price") else price
        item_name = data.get("name", product_name) if data.get("name") else product_name
        
        # Check if item already in cart
        items = cart.get("items", [])
        existing_item = None
        for item in items:
            if item["sku"] == sku:
                existing_item = item
                break
        
        if existing_item:
            # Update quantity
            existing_item["quantity"] += quantity
            existing_item["updated_at"] = datetime.utcnow().isoformat()
            mongo.db.carts.update_one(
                {"_id": ObjectId(cart_id), "items.sku": sku},
                {"$set": {"items.$": existing_item, "updated_at": datetime.utcnow()}}
            )
        else:
            # Add new item
            new_item = {
                "sku": sku,
                "name": item_name,
                "price": float(item_price),
                "quantity": quantity,
                "added_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mongo.db.carts.update_one(
                {"_id": ObjectId(cart_id)},
                {"$push": {"items": new_item}, "$set": {"updated_at": datetime.utcnow()}}
            )
        
        # Recalculate totals
        updated_cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        totals = calculate_cart_totals(
            updated_cart.get("items", []),
            updated_cart.get("discount_code"),
            updated_cart.get("shipping_method", "standard")
        )
        mongo.db.carts.update_one(
            {"_id": ObjectId(cart_id)},
            {"$set": {**totals, "updated_at": datetime.utcnow()}}
        )
        updated_cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        
        return jsonify({
            "message": "Item added to cart",
            "cart": serialize_cart(updated_cart)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/carts/<cart_id>/items/<sku>", methods=["PUT"])
def update_item(cart_id, sku):
    """Update item quantity in cart."""
    try:
        if not ObjectId.is_valid(cart_id):
            return jsonify({"error": "Invalid cart ID format"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        quantity = int(data.get("quantity", 1))
        if quantity < 1:
            return jsonify({"error": "Quantity must be at least 1"}), 400
        
        cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        if not cart:
            return jsonify({"error": "Cart not found"}), 404
        
        # Find and update item
        items = cart.get("items", [])
        item_found = False
        for item in items:
            if item["sku"] == sku:
                item["quantity"] = quantity
                item["updated_at"] = datetime.utcnow().isoformat()
                item_found = True
                break
        
        if not item_found:
            return jsonify({"error": f"Item with SKU '{sku}' not in cart"}), 404
        
        # Update entire items array
        totals = calculate_cart_totals(items, cart.get("discount_code"), cart.get("shipping_method", "standard"))
        mongo.db.carts.update_one(
            {"_id": ObjectId(cart_id)},
            {"$set": {"items": items, **totals, "updated_at": datetime.utcnow()}}
        )
        
        updated_cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        return jsonify({
            "message": "Item quantity updated",
            "cart": serialize_cart(updated_cart)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/carts/<cart_id>/items/<sku>", methods=["DELETE"])
def remove_item(cart_id, sku):
    """Remove an item from the cart."""
    try:
        if not ObjectId.is_valid(cart_id):
            return jsonify({"error": "Invalid cart ID format"}), 400
        
        cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        if not cart:
            return jsonify({"error": "Cart not found"}), 404
        
        # Pull item from array
        mongo.db.carts.update_one(
            {"_id": ObjectId(cart_id)},
            {"$pull": {"items": {"sku": sku}}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        # Recalculate totals
        updated_cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        totals = calculate_cart_totals(
            updated_cart.get("items", []),
            updated_cart.get("discount_code"),
            updated_cart.get("shipping_method", "standard")
        )
        mongo.db.carts.update_one(
            {"_id": ObjectId(cart_id)},
            {"$set": {**totals, "updated_at": datetime.utcnow()}}
        )
        
        updated_cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        return jsonify({
            "message": "Item removed from cart",
            "cart": serialize_cart(updated_cart)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/carts/<cart_id>/apply-coupon", methods=["POST"])
def apply_coupon(cart_id):
    """Apply a discount coupon to the cart."""
    try:
        if not ObjectId.is_valid(cart_id):
            return jsonify({"error": "Invalid cart ID format"}), 400
        
        data = request.get_json()
        code = data.get("code", "").upper().strip() if data else ""
        
        if not code:
            return jsonify({"error": "Coupon code is required"}), 400
        
        if code not in COUPONS:
            return jsonify({"error": f"Invalid coupon code: '{code}'"}), 400
        
        cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        if not cart:
            return jsonify({"error": "Cart not found"}), 404
        
        coupon = COUPONS[code]
        subtotal = sum(item.get("price", 0) * item.get("quantity", 0) for item in cart.get("items", []))
        
        if subtotal < coupon["min_order"]:
            return jsonify({
                "error": f"Order minimum of ${coupon['min_order']} required for this coupon"
            }), 400
        
        # Apply coupon
        totals = calculate_cart_totals(cart.get("items", []), code, cart.get("shipping_method", "standard"))
        mongo.db.carts.update_one(
            {"_id": ObjectId(cart_id)},
            {"$set": {**totals, "discount_code": code, "updated_at": datetime.utcnow()}}
        )
        
        updated_cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        return jsonify({
            "message": f"Coupon '{code}' applied successfully",
            "coupon_details": {
                "code": code,
                "description": coupon["description"],
                "savings": totals["discount"]
            },
            "cart": serialize_cart(updated_cart)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/carts/<cart_id>/shipping", methods=["PUT"])
def update_shipping(cart_id):
    """Update shipping method for the cart."""
    try:
        if not ObjectId.is_valid(cart_id):
            return jsonify({"error": "Invalid cart ID format"}), 400
        
        data = request.get_json()
        method = data.get("method", "standard") if data else "standard"
        
        if method not in ["standard", "express"]:
            return jsonify({"error": "Shipping method must be 'standard' or 'express'"}), 400
        
        cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        if not cart:
            return jsonify({"error": "Cart not found"}), 404
        
        totals = calculate_cart_totals(cart.get("items", []), cart.get("discount_code"), method)
        mongo.db.carts.update_one(
            {"_id": ObjectId(cart_id)},
            {"$set": {**totals, "shipping_method": method, "updated_at": datetime.utcnow()}}
        )
        
        updated_cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        return jsonify({
            "message": f"Shipping method updated to '{method}'",
            "cart": serialize_cart(updated_cart)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/carts/<cart_id>/checkout", methods=["POST"])
def checkout(cart_id):
    """Process cart checkout and create order summary."""
    try:
        if not ObjectId.is_valid(cart_id):
            return jsonify({"error": "Invalid cart ID format"}), 400
        
        data = request.get_json() or {}
        
        cart = mongo.db.carts.find_one({"_id": ObjectId(cart_id)})
        if not cart:
            return jsonify({"error": "Cart not found"}), 404
        
        if not cart.get("items"):
            return jsonify({"error": "Cannot checkout an empty cart"}), 400
        
        # Build order summary
        totals = calculate_cart_totals(
            cart.get("items", []),
            cart.get("discount_code"),
            cart.get("shipping_method", "standard")
        )
        
        order_summary = {
            "cart_id": str(cart_id),
            "user_id": cart.get("user_id"),
            "items": cart.get("items", []),
            **totals,
            "discount_code": cart.get("discount_code", ""),
            "shipping_method": cart.get("shipping_method", "standard"),
            "shipping_address": data.get("shipping_address", {}),
            "billing_address": data.get("billing_address", {}),
            "payment_method": data.get("payment_method", "credit_card"),
            "status": "confirmed",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Mark cart as checked out
        mongo.db.carts.update_one(
            {"_id": ObjectId(cart_id)},
            {"$set": {"status": "checked_out", "updated_at": datetime.utcnow()}}
        )
        
        # Store order
        mongo.db.orders.insert_one(order_summary)
        
        return jsonify({
            "message": "Order placed successfully",
            "order": order_summary
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/carts/<cart_id>", methods=["DELETE"])
def delete_cart(cart_id):
    """Delete a cart permanently."""
    try:
        if not ObjectId.is_valid(cart_id):
            return jsonify({"error": "Invalid cart ID format"}), 400
        
        result = mongo.db.carts.delete_one({"_id": ObjectId(cart_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Cart not found"}), 404
        
        return jsonify({"message": "Cart deleted successfully"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/coupons", methods=["GET"])
def list_coupons():
    """List all available coupons."""
    return jsonify({
        "coupons": [
            {"code": k, **v} for k, v in COUPONS.items()
        ]
    }), 200


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
