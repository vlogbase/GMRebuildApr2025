"""
Test workflow for the Flask application
"""

def run():
    """
    Run the Flask application
    """
    import sys
    import os
    from app import app
    
    print("Starting Flask application testing workflow...")
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()