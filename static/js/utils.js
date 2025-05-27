// Utility function to debounce function calls
export function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Function to get CSRF token from meta tag
export function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content;
}

// Utility function to force a browser repaint on an element
// This is used to fix rendering issues where content doesn't appear until window focus changes
export function forceRepaint(element) {
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