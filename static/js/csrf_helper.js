/**
 * CSRF Protection Helper
 * 
 * This script handles CSRF token management for all AJAX requests in the application.
 * It ensures that every fetch or XMLHttpRequest call includes the CSRF token automatically.
 */

// Get CSRF token from meta tag
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!token) {
        console.warn('CSRF token not found in the document');
    }
    return token;
}

// Create a wrapper around the fetch API that automatically includes the CSRF token
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    // Create a new options object with the default headers
    const newOptions = { ...options };
    
    // Initialize headers if not present
    if (!newOptions.headers) {
        newOptions.headers = {};
    }
    
    // If headers is an object but not a Headers instance, convert it
    if (newOptions.headers && typeof newOptions.headers === 'object' && !(newOptions.headers instanceof Headers)) {
        const headers = new Headers(newOptions.headers);
        
        // Add CSRF token if not already present and the request is non-GET
        if (!headers.has('X-CSRFToken') && (!options.method || options.method.toUpperCase() !== 'GET')) {
            const token = getCSRFToken();
            if (token) {
                headers.append('X-CSRFToken', token);
            }
        }
        
        newOptions.headers = headers;
    } else if (newOptions.headers instanceof Headers) {
        // If it's already a Headers instance, just add the token if needed
        if (!newOptions.headers.has('X-CSRFToken') && (!options.method || options.method.toUpperCase() !== 'GET')) {
            const token = getCSRFToken();
            if (token) {
                newOptions.headers.append('X-CSRFToken', token);
            }
        }
    }
    
    // Call the original fetch with updated options
    return originalFetch(url, newOptions);
};

// Also intercept XMLHttpRequest to ensure legacy AJAX calls include the token
(function() {
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        // Store the method to check if it's non-GET later
        this._method = method;
        
        // Call the original open method
        originalOpen.apply(this, arguments);
    };
    
    const originalSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function(body) {
        // Add CSRF token for non-GET requests if not already set
        if (this._method && this._method.toUpperCase() !== 'GET') {
            try {
                const token = getCSRFToken();
                if (token) {
                    this.setRequestHeader('X-CSRFToken', token);
                }
            } catch (e) {
                console.warn('Failed to set CSRF token header:', e);
                // Continue with the request even if setting the header fails
            }
        }
        
        // Call the original send method
        originalSend.apply(this, arguments);
    };
    
    // Helper method to check if a request header is already set
    XMLHttpRequest.prototype.getRequestHeader = function(name) {
        return this._requestHeaders && this._requestHeaders[name];
    };
    
    // Store headers when they're set
    const originalSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.setRequestHeader = function(name, value) {
        if (!this._requestHeaders) {
            this._requestHeaders = {};
        }
        this._requestHeaders[name] = value;
        
        // Call the original setRequestHeader method
        originalSetRequestHeader.apply(this, arguments);
    };
})();

// Log that the CSRF helper is loaded
console.log('CSRF Helper: Initialized protection for all AJAX requests');