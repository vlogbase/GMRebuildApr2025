"""
Simple Flask server workflow for GloriaMundo
This runs the main application with the fixed affiliate blueprint
"""

def run():
    """Run the Flask application"""
    from app import app
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()