"""
Flask Web UI for the Binance Futures Trading Bot.
Provides a simple REST API and serves a modern frontend.
"""

import os
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify

from bot.config import load_settings, PROJECT_ROOT
from bot.logging_config import setup_logging
from bot.validators import validate_order_params
from bot.client import BinanceClient
from bot.orders import place_order
from bot.exceptions import ConfigurationError, ValidationError, TradingBotError
from bot.utils import ORDER_HISTORY_FILE

app = Flask(__name__)

# Initialize dependencies at startup
try:
    settings = load_settings()
    logger = setup_logging(settings.log_dir, settings.log_level)
    client = BinanceClient(settings)
except ConfigurationError as exc:
    print(f"Failed to start UI: {exc.message}")
    exit(1)


@app.route("/")
def index():
    """Serve the main trading terminal UI."""
    return render_template("index.html")


@app.route("/api/order", methods=["POST"])
def api_place_order():
    """API endpoint to place an order from the Web UI."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON payload provided."}), 400

    try:
        validated = validate_order_params(
            symbol=data.get("symbol"),
            side=data.get("side"),
            order_type=data.get("type"),
            quantity=data.get("quantity"),
            price=data.get("price") if data.get("type") == "LIMIT" else None,
        )
    except ValidationError as exc:
        return jsonify({"error": exc.message}), 400

    try:
        response = place_order(client, validated, PROJECT_ROOT)
        if response:
            return jsonify({
                "message": "Order placed successfully!",
                "data": response
            }), 200
        else:
            return jsonify({"error": "Order failed. Check console/logs for details."}), 500
    except Exception as exc:
        logger.exception("Unexpected error during UI order placement.")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/history", methods=["GET"])
def api_get_history():
    """API endpoint to fetch order history."""
    history_file = PROJECT_ROOT / ORDER_HISTORY_FILE
    if not history_file.exists():
        return jsonify([])
    
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Return reversed so newest are at the top
            return jsonify(list(reversed(data)))
    except Exception as exc:
        return jsonify({"error": "Failed to read order history."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
