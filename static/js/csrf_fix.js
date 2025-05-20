/**
 * CSRF Fix for AJAX Requests
 *
 * This script fixes CSRF token handling for AJAX requests that are receiving 400 Bad Request errors.
 * It ensures that both standard and JavaScript fetch API calls include the correct token format.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Log that the fix is loaded
    console.log('CSRF Fix: Applying enhanced token handling for problematic endpoints');
    
    // The original fetch function from the window object
    const originalFetch = window.fetch;
    
    // Override the fetch function
    window.fetch = function(url, options = {}) {
        // Create a new options object with the default headers
        const newOptions = { ...options };
        
        // A list of problematic endpoints that need special handling
        const problematicEndpoints = [
            '/save_preference',
            '/api/cleanup-empty-conversations',
            '/api/create-conversation'
        ];
        
        // Check if this is a request to a problematic endpoint
        const isProblematicEndpoint = problematicEndpoints.some(endpoint => 
            url.includes(endpoint)
        );
        
        // For our problematic endpoints, ensure consistent header format
        if (isProblematicEndpoint && (!options.method || options.method.toUpperCase() !== 'GET')) {
            // Initialize headers if not present
            if (!newOptions.headers) {
                newOptions.headers = {};
            }
            
            // Get CSRF token from meta tag
            const token = document.querySelector('meta[name="csrf-token"]')?.content;
            
            if (token) {
                console.log(`CSRF Fix: Adding token to request for ${url}`);
                
                // Convert headers to object if it's a Headers instance
                if (newOptions.headers instanceof Headers) {
                    const headerObj = {};
                    for (const [key, value] of newOptions.headers.entries()) {
                        headerObj[key] = value;
                    }
                    newOptions.headers = headerObj;
                }
                
                // Add the token in both header formats that Flask-WTF accepts
                newOptions.headers['X-CSRFToken'] = token;
                newOptions.headers['X-CSRF-Token'] = token;
                
                // For application/json content type, ensure it's explicitly set
                if (!newOptions.headers['Content-Type']) {
                    newOptions.headers['Content-Type'] = 'application/json';
                }
            }
        }
        
        // Call the original fetch with updated options
        return originalFetch(url, newOptions);
    };
});