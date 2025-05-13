"""
Simple Flask server workflow to test the chat rendering fix
"""
from app import app

def run():
    """
    Run the Flask application with the chat rendering fix
    """
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    run()