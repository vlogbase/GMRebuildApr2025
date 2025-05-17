/**
 * Model Fallback Confirmation Dialog
 * 
 * This script handles the model fallback confirmation dialog that appears
 * when a user tries to use a model that's currently unavailable.
 */

// Create the fallback confirmation dialog in the DOM
function createFallbackConfirmationDialog() {
    if (document.getElementById('fallback-dialog')) {
        return; // Dialog already exists
    }

    const dialog = document.createElement('div');
    dialog.id = 'fallback-dialog';
    dialog.className = 'fallback-dialog hidden';
    
    dialog.innerHTML = `
        <div class="fallback-dialog-content">
            <div class="fallback-dialog-header">
                <h3>Model Unavailable</h3>
                <button type="button" class="fallback-close-btn">&times;</button>
            </div>
            <div class="fallback-dialog-body">
                <p>
                    The model you selected <strong id="original-model-name"></strong> is currently unavailable.
                    Would you like to use <strong id="fallback-model-name"></strong> instead?
                </p>
            </div>
            <div class="fallback-dialog-footer">
                <label class="fallback-remember">
                    <input type="checkbox" id="auto-fallback-checkbox">
                    <span>Always use fallback models</span>
                </label>
                <div class="fallback-buttons">
                    <button type="button" class="fallback-btn secondary" id="fallback-no-btn">No</button>
                    <button type="button" class="fallback-btn primary" id="fallback-yes-btn">Yes</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Close dialog when clicking the close button
    const closeButton = dialog.querySelector('.fallback-close-btn');
    closeButton.addEventListener('click', () => {
        hideDialog();
    });
    
    // Setup No button (reject fallback)
    const noButton = dialog.querySelector('#fallback-no-btn');
    noButton.addEventListener('click', () => {
        if (window.fallbackDialogCallback) {
            window.fallbackDialogCallback(false);
        }
        hideDialog();
    });
    
    // Setup Yes button (accept fallback)
    const yesButton = dialog.querySelector('#fallback-yes-btn');
    yesButton.addEventListener('click', () => {
        const autoFallback = document.getElementById('auto-fallback-checkbox').checked;
        
        // Save auto-fallback preference if checked
        if (autoFallback) {
            saveAutoFallbackPreference(true);
        }
        
        if (window.fallbackDialogCallback) {
            window.fallbackDialogCallback(true);
        }
        hideDialog();
    });
    
    // Setup click outside to close
    dialog.addEventListener('click', (e) => {
        if (e.target === dialog) {
            hideDialog();
        }
    });
}

// Show the fallback confirmation dialog
function showFallbackConfirmation(originalModel, fallbackModel, userMessage, callback) {
    createFallbackConfirmationDialog();
    
    // Set model names in the dialog
    document.getElementById('original-model-name').textContent = originalModel;
    document.getElementById('fallback-model-name').textContent = fallbackModel;
    
    // Store callback to be called when user makes a choice
    window.fallbackDialogCallback = callback;
    window.fallbackUserMessage = userMessage;
    
    // Reset checkbox
    document.getElementById('auto-fallback-checkbox').checked = false;
    
    // Show dialog
    const dialog = document.getElementById('fallback-dialog');
    dialog.classList.remove('hidden');
    
    // Focus on the Yes button
    setTimeout(() => {
        document.getElementById('fallback-yes-btn').focus();
    }, 100);
}

// Hide the dialog
function hideDialog() {
    const dialog = document.getElementById('fallback-dialog');
    dialog.classList.add('hidden');
}

// Show a non-blocking notification for auto-fallback scenarios
function showFallbackNotification(originalModel, fallbackModel) {
    // Create notification element if it doesn't exist
    let notification = document.getElementById('fallback-notification');
    
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'fallback-notification';
        notification.className = 'fallback-notification hidden';
        
        notification.innerHTML = `
            <div class="fallback-notification-content">
                <span>Using <strong id="fallback-notification-model"></strong> instead of <strong id="original-notification-model"></strong></span>
                <button type="button" class="fallback-notification-close">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Setup close button
        const closeButton = notification.querySelector('.fallback-notification-close');
        closeButton.addEventListener('click', () => {
            notification.classList.add('hidden');
        });
    }
    
    // Update model names
    document.getElementById('original-notification-model').textContent = originalModel;
    document.getElementById('fallback-notification-model').textContent = fallbackModel;
    
    // Show notification
    notification.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 5000);
}

// Check if user has auto-fallback preference set
function checkAutoFallbackPreference() {
    try {
        return localStorage.getItem('auto_fallback_model') === 'true';
    } catch (e) {
        console.error('Error accessing localStorage:', e);
        return false;
    }
}

// Save user's auto-fallback preference
function saveAutoFallbackPreference(autoFallback) {
    try {
        localStorage.setItem('auto_fallback_model', autoFallback ? 'true' : 'false');
        
        // Update server-side preference if logged in
        if (typeof updateUserPreference === 'function') {
            updateUserPreference('auto_fallback_model', autoFallback ? 'true' : 'false');
        }
    } catch (e) {
        console.error('Error saving to localStorage:', e);
    }
}

// Get CSRF token for API calls
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Check if the user has auto-fallback enabled and callback with result
function shouldAutoFallback(callback) {
    // First check local storage
    const localPreference = checkAutoFallbackPreference();
    
    // If we have a local preference, use it
    if (localPreference !== null) {
        callback(localPreference);
        return;
    }
    
    // Otherwise check the server for user preference if logged in
    if (document.body.classList.contains('user-logged-in')) {
        fetch('/api/user/preferences')
            .then(response => response.json())
            .then(data => {
                const autoFallback = data.preferences?.auto_fallback_model === 'true';
                callback(autoFallback);
            })
            .catch(error => {
                console.error('Error fetching user preferences:', error);
                callback(false); // Default to false on error
            });
    } else {
        // Not logged in, use default (false)
        callback(false);
    }
}

// Initialize the module
document.addEventListener('DOMContentLoaded', () => {
    createFallbackConfirmationDialog();
});