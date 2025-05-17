/**
 * Model Fallback Dialog
 * 
 * This module provides a confirmation dialog when a selected AI model is unavailable
 * and a fallback model needs to be used instead.
 */
(function() {
    'use strict';
    
    // Create namespace for ModelFallback
    window.ModelFallback = {};
    
    // DOM elements (will be initialized when needed)
    let overlayElement = null;
    let dialogElement = null;
    let confirmButton = null;
    let cancelButton = null;
    
    // Callback storage
    let onAcceptCallback = null;
    let onRejectCallback = null;
    
    // Current message and model
    let currentMessage = '';
    let fallbackModelId = '';
    
    /**
     * Create the dialog DOM elements
     */
    function createDialogElements() {
        // Create overlay
        overlayElement = document.createElement('div');
        overlayElement.className = 'fallback-overlay';
        
        // Create dialog
        dialogElement = document.createElement('div');
        dialogElement.className = 'fallback-dialog';
        
        // Add dialog content
        dialogElement.innerHTML = `
            <div class="fallback-header">
                <i class="fas fa-exclamation-triangle"></i>
                <h2 class="fallback-title">Model Unavailable</h2>
            </div>
            
            <div class="fallback-message">
                The model you selected is currently unavailable. Would you like to use
                an alternative model instead?
            </div>
            
            <div class="fallback-model-details">
                <div class="fallback-model-row">
                    <span class="fallback-model-label">Requested:</span>
                    <span class="fallback-model-value original" id="original-model">Claude 3 Haiku</span>
                </div>
                <div class="fallback-model-row">
                    <span class="fallback-model-label">Alternative:</span>
                    <span class="fallback-model-value fallback" id="fallback-model">Gemini Flash</span>
                </div>
            </div>
            
            <div class="fallback-buttons">
                <button class="fallback-button cancel" id="fallback-cancel">No, Cancel</button>
                <button class="fallback-button confirm" id="fallback-confirm">Yes, Use Alternative</button>
            </div>
        `;
        
        // Add dialog to overlay
        overlayElement.appendChild(dialogElement);
        
        // Add overlay to document
        document.body.appendChild(overlayElement);
        
        // Get buttons
        confirmButton = document.getElementById('fallback-confirm');
        cancelButton = document.getElementById('fallback-cancel');
        
        // Add event listeners
        confirmButton.addEventListener('click', handleAccept);
        cancelButton.addEventListener('click', handleReject);
        
        // Close on overlay click (only if clicked outside dialog)
        overlayElement.addEventListener('click', function(e) {
            if (e.target === overlayElement) {
                handleReject();
            }
        });
        
        // Escape key to close
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && overlayElement.classList.contains('active')) {
                handleReject();
            }
        });
        
        console.log('ModelFallback: Dialog elements created');
    }
    
    /**
     * Show the fallback confirmation dialog
     * 
     * @param {string} originalModel - The name of the originally requested model
     * @param {string} fallbackModel - The name of the fallback model
     * @param {string} message - The message to send
     * @param {string} fallbackId - The ID of the fallback model
     */
    window.ModelFallback.showFallbackDialog = function(originalModel, fallbackModel, message, fallbackId) {
        console.log(`ModelFallback: Showing dialog for ${originalModel} -> ${fallbackModel}`);
        
        // Create dialog if it doesn't exist
        if (!overlayElement) {
            createDialogElements();
        }
        
        // Set model names
        document.getElementById('original-model').textContent = originalModel;
        document.getElementById('fallback-model').textContent = fallbackModel;
        
        // Store message and fallback model ID
        currentMessage = message;
        fallbackModelId = fallbackId || fallbackModel;
        
        // Show dialog
        overlayElement.classList.add('active');
        
        // Setup callbacks
        setupCallbacks();
    };
    
    /**
     * Setup callbacks for accept/reject actions
     */
    function setupCallbacks() {
        // Accept callback: Send message with fallback model
        onAcceptCallback = function() {
            console.log(`ModelFallback: User accepted fallback model ${fallbackModelId}`);
            if (typeof window.sendChatMessageWithFallback === 'function') {
                window.sendChatMessageWithFallback(currentMessage, fallbackModelId);
            } else {
                console.error('ModelFallback: sendChatMessageWithFallback function not available');
                alert('Error: Could not send message with fallback model. Please try again.');
            }
        };
        
        // Reject callback: Do nothing, user needs to select a different model
        onRejectCallback = function() {
            console.log('ModelFallback: User rejected fallback model');
            
            // Re-enable input and send button, make sure message is available for resending
            const messageInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            
            if (messageInput && currentMessage) {
                messageInput.value = currentMessage;
                messageInput.disabled = false;
                messageInput.focus();
            }
            
            if (sendButton) {
                sendButton.disabled = false;
            }
        };
    }
    
    /**
     * Handle accept button click
     */
    function handleAccept() {
        // Hide dialog
        overlayElement.classList.remove('active');
        
        // Call accept callback
        if (typeof onAcceptCallback === 'function') {
            onAcceptCallback();
        }
    }
    
    /**
     * Handle reject button click
     */
    function handleReject() {
        // Hide dialog
        overlayElement.classList.remove('active');
        
        // Call reject callback
        if (typeof onRejectCallback === 'function') {
            onRejectCallback();
        }
    }
    
    /**
     * Get the user's auto-fallback preference
     * This checks for the setting in user preferences and returns a boolean
     * 
     * @returns {boolean} - Whether auto-fallback is enabled
     */
    window.ModelFallback.getUserAutoFallbackPreference = function() {
        // Default to false (always show confirmation)
        let autoFallbackEnabled = false;
        
        // Try to get from user data
        try {
            // Check if we have the preference element in the DOM
            const autoFallbackElement = document.getElementById('auto-fallback-enabled');
            if (autoFallbackElement) {
                autoFallbackEnabled = autoFallbackElement.value === 'true';
            } else {
                // If not in DOM, try to get from API (for logged-in users)
                // This is an async call, but we'll return the default for now
                // and update it asynchronously
                fetch('/api/user/chat_settings')
                    .then(response => response.json())
                    .then(data => {
                        if (data && 'auto_fallback_enabled' in data) {
                            autoFallbackEnabled = data.auto_fallback_enabled;
                            console.log(`ModelFallback: Got auto_fallback_enabled=${autoFallbackEnabled} from API`);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching chat settings:', error);
                    });
            }
        } catch (error) {
            console.error('Error getting auto-fallback preference:', error);
        }
        
        console.log(`ModelFallback: auto_fallback_enabled=${autoFallbackEnabled}`);
        return autoFallbackEnabled;
    };
    
    // Log initialization
    console.log('ModelFallback: Module initialized');
})();