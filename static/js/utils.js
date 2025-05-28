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

// Consolidated showToast function with standardized signature
export function showToast(type, message) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        document.body.appendChild(toastContainer);
    }

    // Create a unique ID for this toast
    const toastId = 'toast-' + Date.now();

    // Set color class based on type
    let colorClass = 'bg-primary';
    if (type === 'success') colorClass = 'bg-success';
    else if (type === 'error') colorClass = 'bg-danger';
    else if (type === 'warning') colorClass = 'bg-warning text-dark';

    // Create toast HTML
    const toastHtml = `
        <div id="${toastId}" class="toast ${colorClass} text-white" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    // Add toast to container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    // Initialize and show the toast
    const toastElement = document.getElementById(toastId);
    const bsToast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();

    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}