# Replit Deployment Guide

This guide provides instructions for deploying your application on Replit.

## Deployment Configuration

The application has been set up with the necessary health check endpoints and configuration for successful deployment on Replit. Here's what has been implemented:

1. **Health Check Endpoints**:
   - Root path (`/`) responds to health checks
   - Dedicated `/health` and `/healthz` endpoints added

2. **Deployment Files**:
   - `wsgi.py`: Standard WSGI entry point
   - `gunicorn_config.py`: Optimized Gunicorn configuration
   - `health_check.py`: Health check endpoints

3. **Redis Configuration**:
   - SSL/TLS 1.2 support for Azure Redis Cache
   - Graceful fallback if Redis is unavailable

## Recommended Deployment Steps

1. **Check your `.replit` file**:
   ```
   [deployment]
   run = ["gunicorn", "wsgi:app", "-c", "gunicorn_config.py"]
   
   [[ports]]
   localPort = 5000
   externalPort = 80
   ```

2. **Deploy using one of these commands**:
   - Standard deployment: `gunicorn wsgi:app -c gunicorn_config.py`
   - Alternative deployment: `gunicorn main:app -k gevent -w 2 --timeout 120 --bind 0.0.0.0:5000`

3. **For debugging deployment issues**:
   - Check application logs for errors
   - Test the health check endpoints locally
   - Verify Redis connection with `python test_redis_connection.py`

## Troubleshooting

If you encounter deployment issues:

1. **Timeout Errors**:
   - Reduce the number of Gunicorn workers (try 1-2)
   - Decrease the timeout value in the Gunicorn configuration

2. **Redis Connection Issues**:
   - The application will fall back to filesystem sessions if Redis is unavailable
   - Check the Redis connection parameters in your environment variables

3. **Health Check Failures**:
   - Verify the root path responds correctly to health checks
   - Ensure the application starts without errors under Gunicorn