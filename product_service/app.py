from flask import Flask, jsonify

app = Flask(__name__)

products = [
    {"id": 1, "name": "Laptop", "price": 60000},
    {"id": 2, "name": "Mouse", "price": 1000}
]

@app.route("/products")
def get_products():
    return jsonify(products)

@app.route("/health")
def health():
    return {"status": "UP"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

