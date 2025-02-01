"""
This module defines a Flask application that serves the version of the application.
"""

# pylint: disable=import-error
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/version', methods=['GET'])
def version():
    """
    Handles the /version endpoint and returns the current application version.
    """
    app_version = {"Version": "1.0.0"}
    return jsonify(app_version)

# To run the Flask app on any host, not just 127.0.0.1
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",port="5001")
