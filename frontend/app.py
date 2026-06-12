"""
Frontend Service - EcomOps Platform
====================================
Serves the web UI for the e-commerce platform. Communicates with
product-service and cart-service via internal Kubernetes DNS.

Features:
- Product catalog browser with search, filter, and sort
- Product detail view with reviews
- Shopping cart management
- Coupon application
- Checkout flow
- Responsive design
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from datetime import datetime, timezone
import os
import requests
import logging
from prometheus_flask_exporter import PrometheusMetrics

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("JWT_SECRET", "ecomops-secret-key-2024")
    
    # Service URLs from ConfigMap
    app.product_service_url = os.environ.get(
        "PRODUCT_SERVICE_URL",
        "http://product-service.ecomops.svc.cluster.local:5000"
    )
    app.cart_service_url = os.environ.get(
        "CART_SERVICE_URL",
        "http://cart-service.ecomops.svc.cluster.local:5000"
    )
    app.start_time = datetime.now(timezone.utc)
    
    # Initialize Prometheus Metrics
    metrics = PrometheusMetrics(app)
    metrics.info('app_info', 'Frontend Service', version='1.0.0')
    
    return app


# ---------------------------------------------------------------------------
# Initialize
# ---------------------------------------------------------------------------

app = create_app()


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def product_api(path="", params=None):
    """Make GET request to Product Service."""
    try:
        resp = requests.get(
            f"{app.product_service_url}{path}",
            params=params,
            timeout=10
        )
        return resp.json() if resp.status_code == 200 else {"products": [], "categories": []}
    except requests.RequestException as e:
        logger.error(f"Product service error: {e}")
        return {"products": [], "categories": [], "error": "Product service unavailable"}


def cart_api_post(path, data=None):
    """Make POST request to Cart Service."""
    try:
        resp = requests.post(
            f"{app.cart_service_url}{path}",
            json=data or {},
            timeout=10
        )
        return resp.json(), resp.status_code
    except requests.RequestException as e:
        logger.error(f"Cart service error: {e}")
        return {"error": "Cart service unavailable"}, 503


def cart_api_get(path):
    """Make GET request to Cart Service."""
    try:
        resp = requests.get(f"{app.cart_service_url}{path}", timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except requests.RequestException as e:
        logger.error(f"Cart service error: {e}")
        return {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    """Health check for Kubernetes probes."""
    uptime = (datetime.now(timezone.utc) - app.start_time).total_seconds()
    return jsonify({
        "status": "healthy",
        "service": "frontend",
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@app.route("/")
def index():
    """Homepage with featured products."""
    # Get products
    data = product_api("/products", {"per_page": 12, "page": 1})
    products = data.get("products", [])
    
    # Get categories
    cat_data = product_api("/categories")
    categories = cat_data.get("categories", [])
    
    return render_template(
        "index.html",
        products=products,
        categories=categories,
        page_title="EcomOps Store",
        cart_count=request.args.get("cart_count", 0)
    )


@app.route("/products")
def browse_products():
    """Product listing with search, filter, and pagination."""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 24))
    category = request.args.get("category", "")
    search = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")
    
    params = {
        "page": page,
        "per_page": per_page,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    if category:
        params["category"] = category
    if search:
        params["search"] = search
    if min_price:
        params["min_price"] = min_price
    if max_price:
        params["max_price"] = max_price
    
    data = product_api("/products", params)
    products = data.get("products", [])
    pagination = data.get("pagination", {})
    
    cat_data = product_api("/categories")
    categories = cat_data.get("categories", [])
    
    return render_template(
        "products.html",
        products=products,
        categories=categories,
        pagination=pagination,
        selected_category=category,
        search_query=search,
        sort_by=sort_by,
        sort_order=sort_order,
        min_price=min_price,
        max_price=max_price,
        page_title="Browse Products - EcomOps"
    )


@app.route("/product/<product_id>")
def product_detail(product_id):
    """Product detail page."""
    data = product_api(f"/products/{product_id}")
    
    if "error" in data:
        return render_template("error.html", message="Product not found"), 404
    
    # Get related products (same category)
    related = product_api("/products", {
        "category": data.get("category"),
        "per_page": 4
    }).get("products", [])
    related = [r for r in related if r.get("id") != product_id][:4]
    
    return render_template(
        "product_detail.html",
        product=data,
        related=related,
        page_title=f"{data.get('name', 'Product')} - EcomOps"
    )


@app.route("/cart")
def view_cart():
    """Shopping cart page."""
    cart_id = request.args.get("cart_id", "")
    if not cart_id:
        return render_template("cart.html", cart=None, page_title="Shopping Cart - EcomOps")
    
    cart_data = cart_api_get(f"/carts/{cart_id}")
    
    # Get coupons
    try:
        coupons_resp = requests.get(f"{app.cart_service_url}/coupons", timeout=5)
        coupons = coupons_resp.json().get("coupons", []) if coupons_resp.status_code == 200 else []
    except requests.RequestException as e:
        logger.error(f"Failed to fetch coupons: {e}")
        coupons = []
    
    return render_template(
        "cart.html",
        cart=cart_data,
        coupons=coupons,
        cart_id=cart_id,
        page_title="Shopping Cart - EcomOps"
    )


@app.route("/api/cart/create", methods=["POST"])
def api_create_cart():
    """AJAX: Create a new cart."""
    data, status = cart_api_post("/carts", {"user_id": "guest"})
    return jsonify(data), status


@app.route("/api/cart/<cart_id>/add", methods=["POST"])
def api_add_to_cart(cart_id):
    """AJAX: Add item to cart."""
    sku = request.json.get("sku")
    name = request.json.get("name", "")
    price = request.json.get("price", 0)
    quantity = request.json.get("quantity", 1)
    
    data, status = cart_api_post(f"/carts/{cart_id}/items", {
        "sku": sku,
        "name": name,
        "price": price,
        "quantity": quantity
    })
    return jsonify(data), status


@app.route("/api/cart/<cart_id>/update/<sku>", methods=["PUT"])
def api_update_cart_item(cart_id, sku):
    """AJAX: Update item quantity."""
    quantity = request.json.get("quantity", 1)
    try:
        resp = requests.put(
            f"{app.cart_service_url}/carts/{cart_id}/items/{sku}",
            json={"quantity": quantity},
            timeout=5
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException:
        return jsonify({"error": "Service unavailable"}), 503


@app.route("/api/cart/<cart_id>/remove/<sku>", methods=["DELETE"])
def api_remove_cart_item(cart_id, sku):
    """AJAX: Remove item from cart."""
    try:
        resp = requests.delete(
            f"{app.cart_service_url}/carts/{cart_id}/items/{sku}",
            timeout=5
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException:
        return jsonify({"error": "Service unavailable"}), 503


@app.route("/api/cart/<cart_id>/coupon", methods=["POST"])
def api_apply_coupon(cart_id):
    """AJAX: Apply coupon code."""
    code = request.json.get("code", "").upper()
    data, status = cart_api_post(f"/carts/{cart_id}/apply-coupon", {"code": code})
    return jsonify(data), status


@app.route("/api/cart/<cart_id>/shipping", methods=["PUT"])
def api_update_shipping(cart_id):
    """AJAX: Update shipping method."""
    method = request.json.get("method", "standard")
    try:
        resp = requests.put(
            f"{app.cart_service_url}/carts/{cart_id}/shipping",
            json={"method": method},
            timeout=5
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException:
        return jsonify({"error": "Service unavailable"}), 503


@app.route("/api/cart/<cart_id>/checkout", methods=["POST"])
def api_checkout(cart_id):
    """AJAX: Process checkout."""
    data, status = cart_api_post(f"/carts/{cart_id}/checkout", request.json)
    return jsonify(data), status


@app.route("/api/cart/<cart_id>/data")
def api_get_cart_data(cart_id):
    """AJAX: Get cart data (item count, items, etc.)"""
    data = cart_api_get(f"/carts/{cart_id}")
    return jsonify(data)


@app.route("/checkout/success")
def checkout_success():
    """Checkout success page."""
    order = request.args.get("order", "")
    return render_template("checkout_success.html", order=order, page_title="Order Confirmed - EcomOps")


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found", page_title="404 - EcomOps"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("error.html", message="An internal error occurred", page_title="Error - EcomOps"), 500


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
