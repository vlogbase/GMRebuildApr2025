from app import app

# This file is used by gunicorn to serve the application
# Configure gunicorn in cli with: 
# gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000 wsgi:app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)