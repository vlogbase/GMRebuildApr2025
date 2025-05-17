/**
 * Model Fallback Integration
 * 
 * This file integrates the model fallback confirmation dialog with the main chat interface,
 * intercepting model unavailability errors and showing the fallback confirmation to users.
 */

// Store original message when fallback is needed
let savedUserMessage = "";
let originalModelId = "";
let fallbackModelId = "";

// Flag to prevent duplicate fallback handling
let handlingFallback = false;

/**
 * Initialize fallback integration by setting up necessary event listeners
 */
function initFallbackIntegration() {
    // Listen for model validation errors from the chat system
    document.addEventListener('modelUnavailableError', handleModelUnavailableError);
    
    // Re-initialize when the page content changes (for SPA-like behavior)
    document.addEventListener('DOMContentLoaded', () => {
        console.log('Fallback integration initialized');
    });
}

/**
 * Handle model unavailable error event
 * @param {CustomEvent} event - The model unavailable error event with model details
 */
function handleModelUnavailableError(event) {
    if (handlingFallback) return; // Prevent duplicate handling
    
    handlingFallback = true;
    
    // Extract event details
    const { originalModel, fallbackModel, userMessage } = event.detail;
    
    // Store original message and model IDs for later
    savedUserMessage = userMessage;
    originalModelId = originalModel.id;
    fallbackModelId = fallbackModel.id;
    
    console.log(`Model unavailable: ${originalModel.name}. Suggested fallback: ${fallbackModel.name}`);
    
    // First check if auto-fallback is enabled in user preferences
    checkAutoFallbackPreference(originalModel.name, fallbackModel.name, userMessage);
}

/**
 * Check if auto-fallback is enabled in user preferences
 * @param {string} originalModelName - The name of the original model
 * @param {string} fallbackModelName - The name of the fallback model
 * @param {string} userMessage - The user's message
 */
function checkAutoFallbackPreference(originalModelName, fallbackModelName, userMessage) {
    fetch('/api/fallback/check_preference')
        .then(response => response.json())
        .then(data => {
            if (data.auto_fallback_enabled) {
                // Auto-fallback is enabled, use fallback model automatically
                console.log('Auto-fallback enabled, switching models automatically');
                
                // Show non-blocking notification
                showFallbackNotification(originalModelName, fallbackModelName);
                
                // Switch model and proceed with chat
                switchToFallbackModel();
            } else {
                // Auto-fallback is disabled, show confirmation dialog
                showFallbackConfirmation(originalModelName, fallbackModelName, userMessage, (accepted) => {
                    if (accepted) {
                        // User accepted fallback, switch model
                        switchToFallbackModel();
                    } else {
                        // User declined fallback, return message to input
                        returnMessageToInput(userMessage);
                    }
                    handlingFallback = false;
                });
            }
        })
        .catch(error => {
            console.error('Error checking fallback preference:', error);
            
            // On error, default to showing confirmation dialog
            showFallbackConfirmation(originalModelName, fallbackModelName, userMessage, (accepted) => {
                if (accepted) {
                    switchToFallbackModel();
                } else {
                    returnMessageToInput(userMessage);
                }
                handlingFallback = false;
            });
        });
}

/**
 * Switch to the fallback model and resend the message
 */
function switchToFallbackModel() {
    // Find model selector
    const modelSelector = document.getElementById('model-selector');
    if (!modelSelector) {
        console.error('Model selector not found');
        handlingFallback = false;
        return;
    }
    
    // Set value to fallback model ID
    modelSelector.value = fallbackModelId;
    
    // Trigger change event to update UI
    const changeEvent = new Event('change', { bubbles: true });
    modelSelector.dispatchEvent(changeEvent);
    
    // Resend the message with the new model
    sendMessageWithFallbackModel(savedUserMessage);
    
    handlingFallback = false;
}

/**
 * Send the user's message with the fallback model
 * @param {string} message - The user's message
 */
function sendMessageWithFallbackModel(message) {
    // Find message input
    const messageInput = document.getElementById('message-input');
    if (!messageInput) {
        console.error('Message input not found');
        return;
    }
    
    // Set input value to original message
    messageInput.value = message;
    
    // Find send button
    const sendButton = document.querySelector('.send-button');
    if (!sendButton) {
        console.error('Send button not found');
        return;
    }
    
    // Click send button to resend message
    sendButton.click();
}

/**
 * Return the original message to the input field
 * @param {string} message - The original user message
 */
function returnMessageToInput(message) {
    // Find message input
    const messageInput = document.getElementById('message-input');
    if (!messageInput) {
        console.error('Message input not found');
        return;
    }
    
    // Set input value to original message
    messageInput.value = message;
    messageInput.focus();
    
    // Reset the original model in the selector
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector) {
        modelSelector.value = originalModelId;
        
        // Trigger change event to update UI
        const changeEvent = new Event('change', { bubbles: true });
        modelSelector.dispatchEvent(changeEvent);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initFallbackIntegration);