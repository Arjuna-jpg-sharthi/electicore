"""Consistent API error responses."""

from flask import jsonify


def error(message, status=400):
    return jsonify({"error": message}), status
