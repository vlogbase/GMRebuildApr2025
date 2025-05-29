#!/usr/bin/env python3
"""
Main workflow for the Flask application
"""
import os
import sys

def run():
    """Run the Flask application"""
    os.execv(sys.executable, [sys.executable, "app.py"])

if __name__ == "__main__":
    run()