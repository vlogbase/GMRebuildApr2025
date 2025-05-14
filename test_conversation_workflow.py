"""
Testing workflow for the conversation history tracking fixes
"""

import os
import sys
import logging
from flask import Flask, render_template, request, jsonify
from app import app

def run():
    """
    Run the Flask application to test the conversation tracking fixes
    """
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run()