"""
Simple Flask server to serve the footer test HTML
"""
from flask import Flask, send_file

app = Flask(__name__)

@app.route('/')
def serve_footer_test():
    """Serve the footer test HTML file"""
    return send_file('footer_test.html')

def run():
    """Run the Flask app"""
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    run()