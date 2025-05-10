# GloriaMundo Admin Dashboard

This document outlines the implementation of the GloriaMundo admin dashboard.

## Overview

The admin dashboard provides secure access to system management features for authorized administrators. It uses a minimal implementation that integrates directly with the main application without relying on Flask-Admin extension.

## Security

- Admin access is restricted to specific email addresses (default: `andy@sentigral.com`)
- Custom `admin_required` decorator enforces access control
- Unauthorized access attempts are logged and redirected to the login page or shown a 403 error

## Configuration

To specify admin email addresses, set the `ADMIN_EMAILS` environment variable with a comma-separated list of email addresses:

```
ADMIN_EMAILS=andy@sentigral.com,admin@example.com
```

## Implementation

The admin dashboard is implemented using a blueprint approach:

1. `admin_loader.py` - Core module that registers the admin blueprint and provides basic admin routes
2. Templates in `templates/admin/` directory

## Routes

- `/admin` - Main admin dashboard showing system statistics
- `/admin/check` - Diagnostic page to verify admin access is working
- `/admin-direct` - Alternative route that redirects to the main admin dashboard

## Development Notes

### Multiple Approaches Tested

Several implementations were created and tested:
- Standard Flask-Admin integration (gm_admin.py)
- Standalone admin app (admin_app.py)
- Custom routes implementation (admin_routes.py)
- Minimal blueprint approach (admin_loader.py) - CURRENT IMPLEMENTATION

The minimal blueprint approach was chosen for its simplicity, reliability, and compatibility with the existing application structure.

### Running the Admin Dashboard

Use the provided workflow file:

```
.replit.workflow-simple-admin
```

This will start the server with the necessary environment variables set.

### Adding New Admin Features

To extend the admin dashboard:

1. Add new routes to `admin_loader.py` using the `@admin_bp.route()` decorator
2. Create corresponding templates in the `templates/admin/` directory
3. Update the dashboard to include links to the new features

## Troubleshooting

If the admin dashboard is not accessible:

1. Verify the user is logged in
2. Check the user's email is in the `ADMIN_EMAILS` environment variable
3. Look for error messages in the application logs
4. Try accessing the `/admin-direct` route as an alternative