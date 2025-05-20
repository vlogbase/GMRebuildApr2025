/**
 * CSRF Token Refresh Helper
 * 
 * This script helps handle CSRF token refreshing for forms
 * to prevent "CSRF token expired" errors during form submission.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all forms with csrf_token
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Check if form has a CSRF token input
        const csrfInput = form.querySelector('input[name="csrf_token"]');
        if (!csrfInput) return;
        
        // Add submit event listener
        form.addEventListener('submit', function(e) {
            // Check if token might be stale (older than 30 minutes)
            const now = new Date().getTime();
            const lastRefresh = parseInt(localStorage.getItem('csrf_last_refresh') || '0');
            
            // If token is potentially stale, refresh it before submission
            if (now - lastRefresh > 30 * 60 * 1000) { // 30 minutes
                e.preventDefault(); // Prevent form submission temporarily
                
                // Make AJAX request to get a fresh token
                fetch('/get-csrf-token', {
                    method: 'GET',
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.csrf_token) {
                        // Update the token in the form
                        csrfInput.value = data.csrf_token;
                        
                        // Store the refresh time
                        localStorage.setItem('csrf_last_refresh', now.toString());
                        
                        // Submit the form
                        form.submit();
                    } else {
                        console.error('Failed to refresh CSRF token');
                        // Still submit the form and let the server handle it
                        form.submit();
                    }
                })
                .catch(error => {
                    console.error('Error refreshing CSRF token:', error);
                    // Still submit the form and let the server handle it
                    form.submit();
                });
            }
        });
    });
});