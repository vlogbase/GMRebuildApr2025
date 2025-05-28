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
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeAccountSettings();
});