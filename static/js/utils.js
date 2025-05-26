// Utility Functions Module
// Common utilities used across the application

// Utility function to debounce function calls
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Function to get CSRF token from meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content;
}

// Utility function to force a browser repaint on an element
// This is used to fix rendering issues where content doesn't appear until window focus changes
function forceRepaint(element) {
    if (!element) {
        console.warn('forceRepaint called with null/undefined element');
        return;
    }
    
    // Read layout property to force layout calculation
    const currentHeight = element.offsetHeight;
    // Force a style recalculation with a more substantial change
    element.style.transform = 'translateZ(0)';
    // Use requestAnimationFrame to ensure it processes in the next paint cycle
    requestAnimationFrame(() => {
        element.style.transform = '';
    });
    
    // Log debug info
    console.debug(`forceRepaint applied to element: ${element.className || 'unnamed'}`);
}

// Implement lazy loading for images to improve initial page load
function setupLazyLoading() {
    if ('loading' in HTMLImageElement.prototype) {
        // Browser supports native lazy loading
        console.debug('Using native lazy loading for images');
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            img.loading = 'lazy';
        });
    } else {
        // Fallback for browsers that don't support native lazy loading
        console.debug('Using IntersectionObserver for lazy loading images');
        const lazyImages = document.querySelectorAll('img[data-src]');
        
        if (lazyImages.length > 0) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }
}

// Format message content with proper HTML escaping and formatting
function formatMessage(text) {
    if (!text) return '';
    
    // Basic HTML escaping
    const escapeMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;'
    };
    
    let escaped = text.replace(/[&<>"']/g, (char) => escapeMap[char]);
    
    // Convert line breaks to <br> tags
    escaped = escaped.replace(/\n/g, '<br>');
    
    return escaped;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Add to page
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

// Export functions for use in other modules
window.utils = {
    debounce,
    getCSRFToken,
    forceRepaint,
    setupLazyLoading,
    formatMessage,
    showToast
};