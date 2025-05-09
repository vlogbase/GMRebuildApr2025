# GloriaMundo Admin Dashboard

A secure admin interface for managing the GloriaMundo chatbot platform built with Flask-Admin.

## Features

- **Secure Access Control**: Only authorized administrators (andy@sentigral.com) can access the dashboard
- **Commission Management**: Approve, reject, and process affiliate commissions
- **Affiliate Management**: View and manage affiliate accounts
- **Analytics Views**: Track user token usage and see which AI models are most popular
- **Dashboard Overview**: Get a quick view of key metrics and system health

## Accessing the Admin Dashboard

The admin interface is available at: `/gm-admin`

The old `/admin` route will redirect to the new interface for backward compatibility.

## Running the Admin Dashboard

You can start the admin dashboard by running:

```
./run_admin.sh
```

The dashboard will be available at port 3000.

## Running Admin Tests

To verify that the admin interface is working correctly, run:

```
./run_admin_tests.sh
```

This will run a series of tests to check:
- Admin access control
- Route security 
- Health check endpoints

## Deployment

The admin dashboard is configured to handle deployment health checks. The root endpoint (/) will return a 200 status code for health checks, making it compatible with deployment platforms.

## Security Features

- **Authentication**: Only authenticated users can attempt to access the admin interface
- **Authorization**: Only users with email andy@sentigral.com can access admin functions
- **Configuration**: Admin access is controlled through the `ADMIN_EMAILS` environment variable

## Technical Details

- Built with Flask-Admin using Bootstrap 3 templates
- Custom secure base view with access control
- Specialized views for various data models
- Port 3000 configuration for dedicated admin interface