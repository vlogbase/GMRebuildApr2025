/**
 * Fallback Preferences JavaScript
 * Handles saving and loading user preferences for model fallback confirmation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get references to the auto fallback toggle elements 
    // (there appear to be multiple versions in the HTML)
    const autoFallbackToggles = [
        document.getElementById('autoFallbackToggle'),
        document.getElementById('autoFallbackEnabled')
    ];
    
    // Add event listener to each toggle that exists
    autoFallbackToggles.forEach(toggle => {
        if (toggle) {
            toggle.addEventListener('change', saveAutoFallbackPreference);
        }
    });
    
    // Load initial preference state from API
    loadAutoFallbackPreference();
});

/**
 * Save the user's auto fallback preference when toggled
 */
async function saveAutoFallbackPreference(event) {
    const autoFallbackEnabled = event.target.checked;
    
    try {
        // Make all toggles match the state of the one that was changed
        const autoFallbackToggles = [
            document.getElementById('autoFallbackToggle'),
            document.getElementById('autoFallbackEnabled')
        ];
        
        autoFallbackToggles.forEach(toggle => {
            if (toggle && toggle !== event.target) {
                toggle.checked = autoFallbackEnabled;
            }
        });
        
        // Update the hidden input value if it exists
        const hiddenInput = document.getElementById('auto-fallback-enabled');
        if (hiddenInput) {
            hiddenInput.value = autoFallbackEnabled ? 'true' : 'false';
        }
        
        // Save the preference via the API
        const response = await fetch('/api/fallback/update_preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                auto_fallback_enabled: autoFallbackEnabled
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show success message (optional)
            console.log('Fallback preference saved successfully');
            
            // You could add a toast notification here if desired
            if (typeof showToast === 'function') {
                showToast('Preference saved', 'success');
            }
        } else {
            console.error('Error saving fallback preference:', data.error);
            
            // Revert the toggle if save failed
            event.target.checked = !autoFallbackEnabled;
            
            // Show error message
            if (typeof showToast === 'function') {
                showToast('Error saving preference', 'error');
            }
        }
    } catch (error) {
        console.error('Error saving fallback preference:', error);
        
        // Revert the toggle if save failed
        event.target.checked = !autoFallbackEnabled;
        
        // Show error message
        if (typeof showToast === 'function') {
            showToast('Error saving preference', 'error');
        }
    }
}

/**
 * Load the user's auto fallback preference from the API
 */
async function loadAutoFallbackPreference() {
    try {
        const response = await fetch('/api/fallback/check_preference');
        const data = await response.json();
        
        // Get all toggle elements
        const autoFallbackToggles = [
            document.getElementById('autoFallbackToggle'),
            document.getElementById('autoFallbackEnabled')
        ];
        
        // Update all existing toggles
        autoFallbackToggles.forEach(toggle => {
            if (toggle) {
                toggle.checked = data.auto_fallback_enabled === true;
            }
        });
        
        // Update the hidden input value if it exists
        const hiddenInput = document.getElementById('auto-fallback-enabled');
        if (hiddenInput) {
            hiddenInput.value = data.auto_fallback_enabled ? 'true' : 'false';
        }
        
        console.log('Fallback preference loaded:', data.auto_fallback_enabled);
    } catch (error) {
        console.error('Error loading fallback preference:', error);
    }
}