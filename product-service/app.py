"""
Product Catalog Service - EcomOps Platform
==========================================
Handles all CRUD operations for product catalog.
Integrated with MongoDB and Prometheus metrics.

API Endpoints:
  GET    /health         - Health check
  GET    /metrics        - Prometheus metrics
  GET    /products       - List all products
  POST   /products       - Create a new product
  GET    /products/<id>  - Get a single product
  PUT    /products/<id>  - Update a product
  DELETE /products/<id>  - Delete a product
  GET    /products/category/<cat> - Filter by category
  POST   /products/<id>/review     - Add a review
"""

from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson import ObjectId
from datetime import datetime, timezone
import os
import sys
from prometheus_flask_exporter import PrometheusMetrics

# ---------------------------------------------------------------------------
# Application Factory & Configuration
# ---------------------------------------------------------------------------

def create_app(config_name="production"):
    app = Flask(__name__)
    
    # Load configuration from environment or defaults
    app.config["MONGO_URI"] = build_mongo_uri()
    app.config["JSON_SORT_KEYS"] = False
    
    # Initialize MongoDB
    mongo = PyMongo(app)
    app.mongo = mongo
    
    # Store start time for uptime reporting
    app.start_time = datetime.now(timezone.utc)
    
    # Initialize Prometheus Metrics
    metrics = PrometheusMetrics(app)
    metrics.info('app_info', 'Product Catalog Service', version='1.0.0')
    
    # Ensure indexes exist
    with app.app_context():
        mongo.db.products.create_index("sku", unique=True)
        mongo.db.products.create_index("category")
    
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
# Initialize Flask app
# ---------------------------------------------------------------------------

app = create_app()
mongo = app.mongo


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def serialize_product(product):
    """Convert MongoDB product document to JSON-serializable dict."""
    return {
        "id": str(product["_id"]),
        "sku": product.get("sku", ""),
        "name": product.get("name", ""),
        "description": product.get("description", ""),
        "price": product.get("price", 0.0),
        "category": product.get("category", ""),
        "brand": product.get("brand", ""),
        "stock_quantity": product.get("stock_quantity", 0),
        "images": product.get("images", []),
        "attributes": product.get("attributes", {}),
        "reviews": product.get("reviews", []),
        "rating": product.get("rating", 0.0),
        "is_active": product.get("is_active", True),
        "created_at": product.get("created_at", datetime.now(timezone.utc)).isoformat() if isinstance(product.get("created_at"), datetime) else product.get("created_at"),
        "updated_at": product.get("updated_at", datetime.now(timezone.utc)).isoformat() if isinstance(product.get("updated_at"), datetime) else product.get("updated_at"),
    }


def validate_product_data(data, partial=False):
    """Validate product payload. Returns (is_valid, error_message)."""
    if not partial and "name" not in data:
        return False, "Product name is required"
    if not partial and "price" not in data:
        return False, "Product price is required"
    if "price" in data and (not isinstance(data["price"], (int, float)) or data["price"] < 0):
        return False, "Price must be a non-negative number"
    if "stock_quantity" in data and (not isinstance(data["stock_quantity"], int) or data["stock_quantity"] < 0):
        return False, "Stock quantity must be a non-negative integer"
    if "sku" in data and len(data["sku"]) < 3:
        return False, "SKU must be at least 3 characters"
    return True, None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Kubernetes probes."""
    try:
        # Verify MongoDB connectivity
        mongo.db.command("ping")
        uptime = (datetime.now(timezone.utc) - app.start_time).total_seconds()
        return jsonify({
            "status": "healthy",
            "service": "product-service",
            "version": "1.0.0",
            "uptime_seconds": round(uptime, 2),
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "product-service",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 503


@app.route("/products", methods=["GET"])
def list_products():
    """List all products with optional filtering, pagination, and sorting."""
    try:
        # Query parameters
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)
        category = request.args.get("category")
        brand = request.args.get("brand")
        min_price = request.args.get("min_price", type=float)
        max_price = request.args.get("max_price", type=float)
        search = request.args.get("search")
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")
        
        # Build query filter
        query_filter = {"is_active": True}
        if category:
            query_filter["category"] = category
        if brand:
            query_filter["brand"] = brand
        if min_price is not None or max_price is not None:
            query_filter["price"] = {}
            if min_price is not None:
                query_filter["price"]["$gte"] = min_price
            if max_price is not None:
                query_filter["price"]["$lte"] = max_price
        if search:
            query_filter["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # Sorting
        sort_direction = -1 if sort_order == "desc" else 1
        
        # Pagination
        skip = (page - 1) * per_page
        
        # Execute query
        total = mongo.db.products.count_documents(query_filter)
        products_cursor = mongo.db.products.find(query_filter).sort(sort_by, sort_direction).skip(skip).limit(per_page)
        products = [serialize_product(p) for p in products_cursor]
        
        return jsonify({
            "products": products,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/products", methods=["POST"])
def create_product():
    """Create a new product."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate
        is_valid, error = validate_product_data(data)
        if not is_valid:
            return jsonify({"error": error}), 400
        
        # Generate SKU if not provided
        if "sku" not in data:
            data["sku"] = f"PRD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Check for duplicate SKU
        existing = mongo.db.products.find_one({"sku": data["sku"]})
        if existing:
            return jsonify({"error": f"Product with SKU '{data['sku']}' already exists"}), 409
        
        # Build document
        product_doc = {
            "sku": data["sku"],
            "name": data["name"],
            "description": data.get("description", ""),
            "price": float(data["price"]),
            "category": data.get("category", "uncategorized"),
            "brand": data.get("brand", ""),
            "stock_quantity": int(data.get("stock_quantity", 0)),
            "images": data.get("images", []),
            "attributes": data.get("attributes", {}),
            "reviews": [],
            "rating": 0.0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        result = mongo.db.products.insert_one(product_doc)
        product_doc["_id"] = result.inserted_id
        
        return jsonify({
            "message": "Product created successfully",
            "product": serialize_product(product_doc)
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    """Get a single product by ID."""
    try:
        if not ObjectId.is_valid(product_id):
            return jsonify({"error": "Invalid product ID format"}), 400
        
        product = mongo.db.products.find_one({"_id": ObjectId(product_id), "is_active": True})
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        return jsonify(serialize_product(product)), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    """Update a product by ID."""
    try:
        if not ObjectId.is_valid(product_id):
            return jsonify({"error": "Invalid product ID format"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        is_valid, error = validate_product_data(data, partial=True)
        if not is_valid:
            return jsonify({"error": error}), 400
        
        # Build update document (exclude immutable fields)
        update_data = {"updated_at": datetime.now(timezone.utc)}
        allowed_fields = ["name", "description", "price", "category", "brand",
                         "stock_quantity", "images", "attributes", "is_active"]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        result = mongo.db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404
        
        updated = mongo.db.products.find_one({"_id": ObjectId(product_id)})
        return jsonify({
            "message": "Product updated successfully",
            "product": serialize_product(updated)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Soft-delete a product by setting is_active to False."""
    try:
        if not ObjectId.is_valid(product_id):
            return jsonify({"error": "Invalid product ID format"}), 400
        
        result = mongo.db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404
        
        return jsonify({"message": "Product deleted successfully"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/products/category/<category>", methods=["GET"])
def get_by_category(category):
    """Get products filtered by category."""
    try:
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)
        skip = (page - 1) * per_page
        
        query = {"category": category, "is_active": True}
        total = mongo.db.products.count_documents(query)
        products_cursor = mongo.db.products.find(query).skip(skip).limit(per_page)
        products = [serialize_product(p) for p in products_cursor]
        
        return jsonify({
            "category": category,
            "products": products,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/products/<product_id>/review", methods=["POST"])
def add_review(product_id):
    """Add a review and rating to a product."""
    try:
        if not ObjectId.is_valid(product_id):
            return jsonify({"error": "Invalid product ID format"}), 400
        
        data = request.get_json()
        if not data or "rating" not in data:
            return jsonify({"error": "Rating is required"}), 400
        
        rating = int(data["rating"])
        if not (1 <= rating <= 5):
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
        
        review = {
            "rating": rating,
            "comment": data.get("comment", ""),
            "reviewer": data.get("reviewer", "Anonymous"),
            "created_at": datetime.now(timezone.utc)
        }
        
        # Add review
        mongo.db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$push": {"reviews": review}}
        )
        
        # Recalculate average rating
        product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
        if product and product.get("reviews"):
            avg_rating = sum(r["rating"] for r in product["reviews"]) / len(product["reviews"])
            mongo.db.products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"rating": round(avg_rating, 1)}}
            )
        
        return jsonify({"message": "Review added successfully"}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/categories", methods=["GET"])
def list_categories():
    """List all unique product categories with product counts."""
    try:
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        results = list(mongo.db.products.aggregate(pipeline))
        categories = [{"name": r["_id"], "product_count": r["count"]} for r in results]
        return jsonify({"categories": categories}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
