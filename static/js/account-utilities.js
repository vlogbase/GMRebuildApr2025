/**
 * Account Utilities Module
 * Provides utility functions for the account page
 */

// Utility function for toast notifications
function showToast(type, message) {
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

// Export for global use
window.showToast = showToast;