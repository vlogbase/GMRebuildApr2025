/**
 * Model Fallback User Preferences
 * 
 * This script handles the user preferences for model fallback behavior,
 * allowing users to configure whether they want automatic fallback or
 * manual confirmation.
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on the account page
    if (!document.getElementById('account-preferences')) {
        return;
    }
    
    initializeFallbackPreferences();
});

// Set up the fallback preferences UI in the account page
function initializeFallbackPreferences() {
    // Find the account preferences form
    const preferencesForm = document.getElementById('account-preferences');
    
    if (!preferencesForm) {
        console.warn('Account preferences form not found');
        return;
    }
    
    // Check if the section already exists to avoid duplicates
    if (document.getElementById('fallback-preferences-section')) {
        return;
    }
    
    // Create the model fallback preferences section
    const fallbackSection = document.createElement('div');
    fallbackSection.id = 'fallback-preferences-section';
    fallbackSection.className = 'preference-section';
    
    fallbackSection.innerHTML = `
        <h4>Model Fallback Preferences</h4>
        <div class="form-group">
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="auto_fallback_model" name="auto_fallback_model">
                <label class="form-check-label" for="auto_fallback_model">
                    Automatically use fallback models when selected model is unavailable
                </label>
            </div>
            <small class="form-text text-muted">
                When enabled, the system will automatically use the next best available model when your selected model is unavailable. 
                When disabled, you'll be asked to confirm before using a fallback model.
            </small>
        </div>
    `;
    
    // Add the section to the form (before the submit button)
    const submitButton = preferencesForm.querySelector('button[type="submit"]');
    if (submitButton) {
        preferencesForm.insertBefore(fallbackSection, submitButton);
    } else {
        preferencesForm.appendChild(fallbackSection);
    }
    
    // Set initial value from user preferences
    fetchUserPreference('auto_fallback_model', function(value) {
        document.getElementById('auto_fallback_model').checked = value === 'true';
    });
    
    // Add event listener for the checkbox to save preference in local storage
    document.getElementById('auto_fallback_model').addEventListener('change', function(e) {
        localStorage.setItem('auto_fallback_model', e.target.checked ? 'true' : 'false');
    });
    
    // Make sure the form submission handler includes our preference
    addFallbackPreferenceToFormSubmission(preferencesForm);
}

// Add our preference to the form submission handler
function addFallbackPreferenceToFormSubmission(form) {
    // Save original submit handler
    const originalSubmitHandler = form.onsubmit;
    
    // Create new submit handler
    form.onsubmit = function(e) {
        // Get all form data
        const formData = new FormData(form);
        
        // Add auto fallback preference (handle unchecked checkbox)
        const autoFallbackCheckbox = document.getElementById('auto_fallback_model');
        if (autoFallbackCheckbox) {
            formData.set('auto_fallback_model', autoFallbackCheckbox.checked ? 'true' : 'false');
        }
        
        // Convert to JSON
        const preferencesData = {};
        for (const [key, value] of formData.entries()) {
            preferencesData[key] = value;
        }
        
        // Submit using fetch API
        fetch('/api/user/preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(preferencesData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Preferences saved successfully');
            } else {
                showToast('Error saving preferences: ' + (data.error || 'Unknown error'), true);
            }
        })
        .catch(error => {
            console.error('Error saving preferences:', error);
            showToast('Error saving preferences: ' + error.message, true);
        });
        
        // Prevent default form submission
        e.preventDefault();
        return false;
    };
}

// Fetch a user preference from the server
function fetchUserPreference(preferenceName, callback) {
    fetch('/api/user/preferences')
        .then(response => response.json())
        .then(data => {
            if (data.preferences && data.preferences[preferenceName] !== undefined) {
                callback(data.preferences[preferenceName]);
            } else {
                // Use local storage as fallback
                const localValue = localStorage.getItem(preferenceName);
                callback(localValue || 'false');
            }
        })
        .catch(error => {
            console.error('Error fetching user preferences:', error);
            // Use local storage as fallback
            const localValue = localStorage.getItem(preferenceName);
            callback(localValue || 'false');
        });
}

// Update a single user preference on the server
function updateUserPreference(preferenceName, value) {
    // Store locally first
    localStorage.setItem(preferenceName, value);
    
    // Only update on server if user is logged in
    if (!document.body.classList.contains('user-logged-in')) {
        return Promise.resolve({ success: true });
    }
    
    const data = {};
    data[preferenceName] = value;
    
    return fetch('/api/user/preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .catch(error => {
        console.error('Error updating user preference:', error);
        return { success: false, error: error.message };
    });
}

// Helper function to show toast notification
function showToast(message, isError = false) {
    const toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) {
        // Create toast container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast ${isError ? 'bg-danger text-white' : 'bg-success text-white'}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${isError ? 'Error' : 'Success'}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add toast to container
    document.getElementById('toast-container').appendChild(toast);
    
    // Initialize and show toast
    const toastElement = new bootstrap.Toast(toast);
    toastElement.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Get CSRF token for secure requests
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}