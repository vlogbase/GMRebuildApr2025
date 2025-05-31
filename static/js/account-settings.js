/**
 * Account Settings Module
 * Handles account settings functionality including conversation clearing
 */

import { showToast } from './utils.js';

function initializeAccountSettings() {
    // Clear conversations functionality
    const clearConversationsBtn = document.getElementById('clearConversationsBtn');
    
    if (clearConversationsBtn) {
        clearConversationsBtn.addEventListener('click', function() {
            // Show confirmation dialog
            if (confirm('Are you sure you want to delete all conversations? This action cannot be undone.')) {
                // User confirmed, send request to clear conversations
                fetch('/clear-conversations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (window.showToast) {
                            showToast('success', 'All conversations have been cleared successfully.');
                        } else {
                            alert('All conversations have been cleared successfully.');
                        }
                    } else {
                        if (window.showToast) {
                            showToast('error', 'Error clearing conversations: ' + (data.error || 'Unknown error'));
                        } else {
                            alert('Error clearing conversations: ' + (data.error || 'Unknown error'));
                        }
                    }
                })
                .catch(error => {
                    console.error('Error clearing conversations:', error);
                    if (window.showToast) {
                        showToast('error', 'Error clearing conversations. Please try again later.');
                    } else {
                        alert('Error clearing conversations. Please try again later.');
                    }
                });
            }
        });
    }

    // Initialize preference toggles
    initializePreferenceToggles();
}

function initializePreferenceToggles() {
    // Memory preference toggle
    const enableMemoryToggle = document.getElementById('enableMemory');
    if (enableMemoryToggle) {
        enableMemoryToggle.addEventListener('change', function() {
            updatePreference('memory', this.checked, '/billing/update-memory-preference', 'enable_memory');
        });
    }

    // Model fallback preference toggle
    const enableModelFallbackToggle = document.getElementById('enableModelFallback');
    if (enableModelFallbackToggle) {
        enableModelFallbackToggle.addEventListener('change', function() {
            updatePreference('model fallback', this.checked, '/billing/update-fallback-preference', 'enable_model_fallback');
        });
    }

    // Identity prompt preference toggle
    const enableIdentityPromptToggle = document.getElementById('enableIdentityPrompt');
    if (enableIdentityPromptToggle) {
        enableIdentityPromptToggle.addEventListener('change', function() {
            updatePreference('identity prompt', this.checked, '/billing/update-identity-prompt-preference', 'enable_identity_prompt');
        });
    }
}

function updatePreference(preferenceName, enabled, endpoint, paramName) {
    const payload = {};
    payload[paramName] = enabled;

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const status = enabled ? 'enabled' : 'disabled';
            if (window.showToast) {
                showToast('success', `${preferenceName} ${status} successfully.`);
            }
        } else {
            if (window.showToast) {
                showToast('error', 'Error updating preference: ' + (data.message || 'Unknown error'));
            } else {
                alert('Error updating preference: ' + (data.message || 'Unknown error'));
            }
            // Revert the toggle if the update failed
            const toggle = document.getElementById(paramName.replace('enable_', 'enable'));
            if (toggle) {
                toggle.checked = !enabled;
            }
        }
    })
    .catch(error => {
        console.error('Error updating preference:', error);
        if (window.showToast) {
            showToast('error', 'Error updating preference. Please try again later.');
        } else {
            alert('Error updating preference. Please try again later.');
        }
        // Revert the toggle if the update failed
        const toggle = document.getElementById(paramName.replace('enable_', 'enable'));
        if (toggle) {
            toggle.checked = !enabled;
        }
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeAccountSettings();
});