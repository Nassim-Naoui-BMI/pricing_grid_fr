from flask import Flask, render_template, jsonify
from src.pricing_grid_fr.data_loader import DataLoader

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/customer/catalogue", methods=["GET"])
def get_customer_catalogue():
    catalogue = DataLoader()._generate_customer_catalogue()
    return catalogue, 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
