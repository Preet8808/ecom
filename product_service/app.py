from flask import Flask, jsonify

app = Flask(__name__)

products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 60000
    },
    {
        "id": 2,
        "name": "Mouse",
        "price": 1000
    },
    {
        "id": 3,
        "name": "Keyboard",
        "price": 2500
    }
]

cart = []


@app.route("/")
def home():
    return jsonify({
        "service": "ecommerce-microservice",
        "status": "running"
    })


@app.route("/products")
def get_products():
    return jsonify(products)


@app.route("/cart")
def get_cart():
    return jsonify(cart)


@app.route("/health")
def health():
    return jsonify({
        "status": "UP"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
